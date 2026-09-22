-- Run: lua tests/action_text.lua   (Lua 5.1, from the pack root)
local files = {"text/Phrases.lua", "text/Tags.lua", "text/Actions.lua", "text/Engine.lua",
	"Options.lua", "Commands.lua"}

local frames = {}
_G.CreateFrame = function()
	local frame = {events = {}}
	function frame:RegisterEvent(event) self.events[event] = true end
	function frame:UnregisterAllEvents() self.events = {} end
	function frame:SetScript(_, fn) self.handler = fn end
	frames[#frames + 1] = frame
	return frame
end

local function fire(event, arg)
	for _, frame in ipairs(frames) do
		if frame.events[event] and frame.handler then
			frame.handler(frame, event, arg)
		end
	end
end

local printed = {}
local realPrint = print
_G.print = function(line) printed[#printed + 1] = line end
local function takePrinted()
	local lines = printed
	printed = {}
	return lines
end

local popups = 0
_G.StaticPopupDialogs = {}
_G.StaticPopup_Show = function() popups = popups + 1 end
_G.ReloadUI = function() end
_G.PlaySoundFile = function() end
_G.SlashCmdList = {}
_G.CreateSettingsButtonInitializer = function() return {} end

local callbacks, proxies = {}, {}
_G.Settings = {
	VarType = {Boolean = "boolean", String = "string"},
	RegisterVerticalLayoutCategory = function(name)
		return {name = name}, {AddInitializer = function() end}
	end,
	RegisterAddOnSetting = function(_, variable, key, tbl, _, _, default)
		if tbl[key] == nil then tbl[key] = default end
		return {GetVariable = function() return variable end}
	end,
	RegisterProxySetting = function(_, variable, _, _, _, getValue, setValue)
		proxies[variable] = {get = getValue, set = setValue}
		return {GetVariable = function() return variable end}
	end,
	CreateCheckbox = function() end,
	CreateDropdown = function(_, _, optionsFn) optionsFn() end,
	CreateControlTextContainer = function()
		local container = {}
		function container:Add() end
		function container:GetData() return {} end
		return container
	end,
	SetOnValueChangedCallback = function(variable, fn) callbacks[variable] = fn end,
	RegisterAddOnCategory = function() end,
}

local role = "dps"
local renames = {}
local loadedMods = {
	{specwarns = {
		{voiceFile = "aesoon", spellId = 1286860},
		{voiceFile = "defensive", spellId = 1298367},
		{voiceFile = "bombyou", spellId = 1286895},
		{voiceFile = "range5", spellId = 2001},
		{voiceFile = "gathershare", spellId = 1295905},
		{voiceFile = "artillery", spellId = 2002},
		{voiceFile = "nosuchkey", spellId = 999},
		{spellId = 111},
	}},
	{},
}
_G.DBM = {
	Mods = {},
	Options = {SpecialWarningShortText = true, ShortTimerText = true},
	-- DBM keeps the first default registered for a spell; a later writer is ignored.
	AddRename = function(_, spellId, text)
		if renames[spellId] == nil then renames[spellId] = text end
	end,
	IsTank = function() return role == "tank" end,
	IsHealer = function() return role == "healer" end,
}

local ns = {}
for _, file in ipairs(files) do
	assert(loadfile(file), "cannot load " .. file)("DBM-VPUkrainianTTS", ns)
end

local phrases = 0
for _ in pairs(ns.phraseByVoice) do phrases = phrases + 1 end
assert(phrases > 400, "phrase table looks truncated: " .. phrases)

for key in pairs(ns.tagByVoice) do
	assert(ns.phraseByVoice[key], "tagged key has no phrase: " .. key)
end
for key, action in pairs(ns.actionByVoice) do
	assert(ns.phraseByVoice[key], "action key has no phrase: " .. key)
	assert(type(action[1]) == "string" and action[1] ~= "", "empty tag for " .. key)
	assert(type(action[2]) == "string" and action[2] ~= "", "empty phrase for " .. key)
	if action[3] then
		for variantRole, text in pairs(action[3]) do
			assert(variantRole == "tank" or variantRole == "healer" or variantRole == "dps",
				"unknown role '" .. tostring(variantRole) .. "' on " .. key)
			assert(type(text) == "string" and text ~= "", "empty role phrase on " .. key)
		end
	end
end

-- the migration from the first version's boolean
DBMVPUkrainianTTSDB = {showTags = false}
assert(ns.DB().format == "phrase", tostring(ns.DB().format))
assert(ns.DB().showTags == nil, "the migrated key must be dropped")
DBMVPUkrainianTTSDB = {showTags = true}
assert(ns.DB().format == "tagphrase", tostring(ns.DB().format))
DBMVPUkrainianTTSDB = {showTags = true, format = "tag"}
assert(ns.DB().format == "tag", "an existing format must survive the migration")
DBMVPUkrainianTTSDB = nil
assert(ns.DB().format == "tagphrase", "a fresh profile defaults to tag plus phrase")

ns.DB().actionText = false
fire("PLAYER_LOGIN")
assert(next(renames) == nil, "nothing may be renamed while the feature is off")
assert(not ns.applied, "nothing was registered, so the reload flag must stay down")

-- no boss mod is loaded yet: the pass must register nothing and claim nothing
ns.DB().actionText = true
fire("PLAYER_LOGIN")
assert(next(renames) == nil, "an empty DBM.Mods has nothing to rename")
assert(not ns.applied)

DBM.Mods = loadedMods
fire("ADDON_LOADED", "DBM-Party-Midnight")
assert(ns.applied, "a registered rename must raise the flag the options panel reads")
assert(ns.appliedRole == "dps", tostring(ns.appliedRole))
assert(ns.appliedRoleVariants, "defensive carries role variants, so the flag must be up")
assert(renames[1286860] == "АОЕ | Скоро шкода по площі", tostring(renames[1286860]))
assert(renames[1298367] == "ТАНК | Танк під ударом", tostring(renames[1298367]))
assert(renames[1286895] == "ВІДІЙДИ | Бомба на тобі, відбіжи від групи", tostring(renames[1286895]))
assert(renames[2001] == "РОЗІЙДІТЬСЯ | Розійдіться на 5 метрів", tostring(renames[2001]))
assert(renames[1295905] == "ЗБЕРІТЬСЯ | Зберіться, ділимо шкоду", tostring(renames[1295905]))
assert(renames[2002] == "Артилерія", tostring(renames[2002]))
assert(renames[999] == nil, "an unknown voice key must be left alone")
assert(renames[111] == nil, "a warning without a voice key must be left alone")

-- a rename another addon got in first with must survive
renames[1286860] = "чуже перейменування"
fire("ADDON_LOADED", "DBM-Raids-Midnight")
assert(renames[1286860] == "чуже перейменування", "the default layer is first writer wins")
renames[1286860] = "АОЕ | Скоро шкода по площі"

-- the three formats
ns.DB().format = "tag"
assert(ns.TextFor("aesoon") == "АОЕ", ns.TextFor("aesoon"))
assert(ns.TextFor("artillery") == "Артилерія", "a key with no tag keeps its phrase in tag mode")
ns.DB().format = "phrase"
assert(ns.TextFor("aesoon") == "Скоро шкода по площі", ns.TextFor("aesoon"))
ns.DB().format = "tagphrase"

-- the role variants
role = "tank"
assert(ns.Role() == "tank")
assert(ns.TextFor("defensive") == "ТАНК | Прожми захист", ns.TextFor("defensive"))
assert(ns.TextFor("tankheal") == "ТАНК | Лікуй танка", ns.TextFor("tankheal"))
role = "healer"
assert(ns.Role() == "healer")
assert(ns.TextFor("defensive") == "ТАНК | Танк під ударом", ns.TextFor("defensive"))
assert(ns.TextFor("healfull") == "АОЕ | Відлікуй до повного", ns.TextFor("healfull"))
role = "dps"
assert(ns.TextFor("healfull") == "АОЕ | Скоро сильна шкода", ns.TextFor("healfull"))
assert(ns.TextFor("watchstep") == "УХИЛЯЙСЯ | Дивись, куди стаєш", "a key without variants is role blind")

-- every tag the data uses reaches the options tooltip
local listed = {}
for _, tag in ipairs(ns.TagList()) do listed[tag] = true end
for key, action in pairs(ns.actionByVoice) do
	assert(listed[action[1]], "tag missing from the list shown to players: " .. action[1] .. " (" .. key .. ")")
end

local nonDbm = {}
for spellId in pairs(renames) do nonDbm[spellId] = true end
fire("ADDON_LOADED", "Details")
for spellId in pairs(renames) do
	assert(nonDbm[spellId], "a non-DBM addon must not trigger a pass")
end

-- the options panel
takePrinted()
fire("ADDON_LOADED", "DBM-VPUkrainianTTS")
assert(callbacks["DBM_VP_UKRAINIANTTS_ACTION_TEXT"], "the panel must register its callbacks")
assert(proxies["DBM_VP_UKRAINIANTTS_KEEP_BAR_NAMES"], "the bar-name checkbox must be a live proxy")

local bars = proxies["DBM_VP_UKRAINIANTTS_KEEP_BAR_NAMES"]
DBM.Options.ShortTimerText = true
assert(bars.get() == false, "the proxy reads DBM at call time")
DBM.Options.ShortTimerText = false
assert(bars.get() == true, "a change made in DBM's own panel is picked up without a reload")
bars.set(false)
assert(DBM.Options.ShortTimerText == true, "unchecking it hands the bars back to DBM's renames")

local onChanged = callbacks["DBM_VP_UKRAINIANTTS_ACTION_TEXT"]
local onFormat = callbacks["DBM_VP_UKRAINIANTTS_FORMAT"]
local settingStub = function(variable) return {GetVariable = function() return variable end} end

popups = 0
onChanged(nil, settingStub("DBM_VP_UKRAINIANTTS_ACTION_TEXT"), true)
assert(popups == 0, "switching the text on never asks for a reload")

popups = 0
onFormat(nil, settingStub("DBM_VP_UKRAINIANTTS_FORMAT"), "tag")
assert(popups == 1, "a format change after renames were registered needs a reload")

-- the same panel before any boss mod loaded: no reload prompt, an explanation instead
ns.applied, ns.appliedRole, ns.appliedRoleVariants = nil, nil, nil
DBM.Mods = {}
popups = 0
takePrinted()
onChanged(nil, settingStub("DBM_VP_UKRAINIANTTS_ACTION_TEXT"), true)
assert(popups == 0, "nothing was registered, so there is nothing to reload for")
assert(#takePrinted() == 1, "the player is told the text waits for a boss mod")
popups = 0
onFormat(nil, settingStub("DBM_VP_UKRAINIANTTS_FORMAT"), "phrase")
assert(popups == 0, "a format change before anything applied needs no reload")
ns.DB().format = "tagphrase"

-- DBM's own rename switch is off: say so instead of failing silently
DBM.Mods = loadedMods
DBM.Options.SpecialWarningShortText = false
takePrinted()
onChanged(nil, settingStub("DBM_VP_UKRAINIANTTS_ACTION_TEXT"), true)
assert(#takePrinted() == 1, "the player is told DBM will not show the rename")
DBM.Options.SpecialWarningShortText = true

-- the slash command
takePrinted()
SlashCmdList["DBMVPUKRAINIANTTS"]("off")
assert(not ns.DB().actionText, "/uatext off must switch the feature off")
assert(#takePrinted() == 2, "off says so and asks for the reload the renames need")
SlashCmdList["DBMVPUKRAINIANTTS"]("on")
assert(ns.DB().actionText, "/uatext on must switch it back on")
assert(#takePrinted() == 1, "on has nothing left to warn about")
SlashCmdList["DBMVPUKRAINIANTTS"]("")
assert(not ns.DB().actionText, "a bare /uatext toggles")
takePrinted()
SlashCmdList["DBMVPUKRAINIANTTS"]("nonsense")
assert(#takePrinted() == 1, "an unknown argument prints the usage line")

_G.print = realPrint
print("ok")
