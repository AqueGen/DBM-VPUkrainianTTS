-- Run: lua tests/action_text.lua   (Lua 5.1, from the pack root)
local files = {"text/Phrases.lua", "text/Actions.lua", "text/Engine.lua", "Options.lua"}

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

local callbacks = {}
_G.Settings = {
	VarType = {Boolean = "boolean", String = "string"},
	RegisterVerticalLayoutCategory = function(name) return {name = name} end,
	RegisterAddOnSetting = function(_, variable, key, tbl, _, _, default)
		if tbl[key] == nil then tbl[key] = default end
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

local renames = {}
local loadedMods = {
	{specwarns = {
		{voiceFile = "aesoon", spellId = 1286860},
		{voiceFile = "defensive", spellId = 1298367},
		{voiceFile = "artillery", spellId = 2002},
		{voiceFile = "nosuchkey", spellId = 999},
		{spellId = 111},
	}},
	{},
}
_G.DBM = {
	Mods = {},
	Options = {SpecialWarningShortText = true},
	-- DBM keeps the first default registered for a spell; a later writer is ignored.
	AddRename = function(_, spellId, text)
		if renames[spellId] == nil then renames[spellId] = text end
	end,
}

local ns = {}
for _, file in ipairs(files) do
	assert(loadfile(file), "cannot load " .. file)("DBM-VPUkrainianTTS", ns)
end

local phrases = 0
for _ in pairs(ns.phraseByVoice) do phrases = phrases + 1 end
assert(phrases > 400, "phrase table looks truncated: " .. phrases)

for key, action in pairs(ns.actionByVoice) do
	assert(ns.phraseByVoice[key], "action key has no phrase: " .. key)
	assert(type(action[1]) == "string" and action[1] ~= "", "empty tag for " .. key)
	assert(type(action[2]) == "string" and action[2] ~= "", "empty phrase for " .. key)
	assert(action[3] == nil, "the role layer is gone, no third element belongs here: " .. key)
end

-- the boolean from the first version becomes the format string
DBMVPUkrainianTTSDB = {showTags = false}
assert(ns.DB().format == "phrase", tostring(ns.DB().format))
assert(ns.DB().showTags == nil, "the migrated key must be dropped")
DBMVPUkrainianTTSDB = {showTags = true, format = "tag"}
assert(ns.DB().format == "tag", "an existing format must survive the migration")
DBMVPUkrainianTTSDB = nil
assert(ns.DB().format == "tagphrase", "a fresh profile defaults to tag plus phrase")

ns.DB().actionText = false
DBM.Mods = loadedMods
fire("PLAYER_LOGIN")
assert(next(renames) == nil, "nothing may be renamed while the feature is off")
assert(not ns.applied, "nothing was registered, so the reload flag must stay down")

ns.DB().actionText = true
fire("ADDON_LOADED", "DBM-Party-Midnight")
assert(ns.applied, "a registered rename must raise the flag the options panel reads")
assert(renames[1286860] == "АОЕ | Скоро шкода по площі", tostring(renames[1286860]))
assert(renames[1298367] == "ТАНК | Танкбастер", tostring(renames[1298367]))
assert(renames[2002] == "Артилерія", "a key with no curated action falls back to the spoken phrase")
assert(renames[999] == nil, "an unknown voice key must be left alone")
assert(renames[111] == nil, "a warning without a voice key must be left alone")

renames[1286860] = "чуже перейменування"
fire("ADDON_LOADED", "DBM-Raids-Midnight")
assert(renames[1286860] == "чуже перейменування", "the default layer is first writer wins")

local before = {}
for spellId in pairs(renames) do before[spellId] = true end
fire("ADDON_LOADED", "Details")
for spellId in pairs(renames) do
	assert(before[spellId], "a non-DBM addon must not trigger a pass")
end

-- the three formats
ns.DB().format = "tag"
assert(ns.TextFor("aesoon") == "АОЕ", ns.TextFor("aesoon"))
assert(ns.TextFor("artillery") == "Артилерія", "a key with no tag keeps its phrase in tag mode")
ns.DB().format = "phrase"
assert(ns.TextFor("aesoon") == "Скоро шкода по площі", ns.TextFor("aesoon"))
ns.DB().format = "tagphrase"
assert(ns.TextFor("aesoon") == "АОЕ | Скоро шкода по площі", ns.TextFor("aesoon"))

-- the options panel
fire("ADDON_LOADED", "DBM-VPUkrainianTTS")
local settingStub = function(variable) return {GetVariable = function() return variable end} end
local onChanged = callbacks["DBM_VP_UKRAINIANTTS_ACTION_TEXT"]
local onFormat = callbacks["DBM_VP_UKRAINIANTTS_FORMAT"]
assert(onChanged and onFormat, "the panel must register both callbacks")

popups = 0
takePrinted()
onChanged(nil, settingStub("DBM_VP_UKRAINIANTTS_ACTION_TEXT"), true)
assert(popups == 0, "switching the text on never asks for a reload")

popups = 0
onFormat(nil, settingStub("DBM_VP_UKRAINIANTTS_FORMAT"), "tag")
assert(popups == 1, "a format change after renames were registered needs a reload")

popups = 0
onChanged(nil, settingStub("DBM_VP_UKRAINIANTTS_ACTION_TEXT"), false)
assert(popups == 1, "switching it off asks for the reload the renames need")

-- before any boss mod loaded there is nothing to reload for, so say so instead
ns.applied = nil
DBM.Mods = {}
popups = 0
takePrinted()
onChanged(nil, settingStub("DBM_VP_UKRAINIANTTS_ACTION_TEXT"), true)
assert(popups == 0, "nothing was registered, so no reload is demanded")
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

_G.print = realPrint
print("ok")
