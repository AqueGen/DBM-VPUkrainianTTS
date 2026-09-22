-- Run: lua tests/action_text.lua   (Lua 5.1, from the pack root)
local files = {"text/Phrases.lua", "text/Tags.lua", "text/Actions.lua", "text/Engine.lua", "Commands.lua"}

local handler
_G.CreateFrame = function()
	return {
		RegisterEvent = function() end,
		UnregisterAllEvents = function() end,
		SetScript = function(_, _, fn) handler = fn end,
	}
end
_G.SlashCmdList = {}

local role = "dps"
local renames = {}
_G.DBM = {
	Mods = {
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
	},
	AddRename = function(_, spellId, text) renames[spellId] = text end,
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

-- the old boolean setting becomes the new format string
DBMVPUkrainianTTSDB = {showTags = false}
assert(ns.DB().format == "phrase", tostring(ns.DB().format))
assert(ns.DB().showTags == nil, "the migrated key must be dropped")
DBMVPUkrainianTTSDB = nil
assert(ns.DB().format == "tagphrase", "a fresh profile defaults to tag plus phrase")

ns.DB().actionText = false
handler(nil, "PLAYER_LOGIN")
assert(next(renames) == nil, "nothing may be renamed while the feature is off")
assert(not ns.applied, "nothing was registered, so the reload flag must stay down")

ns.DB().actionText = true
handler(nil, "PLAYER_LOGIN")
assert(ns.applied, "a registered rename must raise the flag the options panel reads")
assert(ns.appliedRole == "dps", tostring(ns.appliedRole))
assert(renames[1286860] == "АОЕ | Скоро шкода по площі", tostring(renames[1286860]))
assert(renames[1298367] == "ТАНК | Танк під ударом", tostring(renames[1298367]))
assert(renames[1286895] == "ВІДІЙДИ | Бомба на тобі, відбіжи від групи", tostring(renames[1286895]))
assert(renames[2001] == "РОЗІЙДІТЬСЯ | Розійдіться на 5 метрів", tostring(renames[2001]))
assert(renames[1295905] == "ЗБЕРІТЬСЯ | Зберіться, ділимо шкоду", tostring(renames[1295905]))
assert(renames[2002] == "Артилерія", tostring(renames[2002]))
assert(renames[999] == nil, "an unknown voice key must be left alone")
assert(renames[111] == nil, "a warning without a voice key must be left alone")

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

renames = {}
handler(nil, "ADDON_LOADED", "Details")
assert(next(renames) == nil, "a non-DBM addon must not trigger a pass")
handler(nil, "ADDON_LOADED", "DBM-Party-Midnight")
assert(renames[1286860] == "АОЕ | Скоро шкода по площі")

-- the slash command
local printed = {}
local realPrint = print
_G.print = function(line) printed[#printed + 1] = line end
SlashCmdList["DBMVPUKRAINIANTTS"]("off")
assert(not ns.DB().actionText, "/uatext off must switch the feature off")
SlashCmdList["DBMVPUKRAINIANTTS"]("on")
assert(ns.DB().actionText, "/uatext on must switch it back on")
SlashCmdList["DBMVPUKRAINIANTTS"]("")
assert(not ns.DB().actionText, "a bare /uatext toggles")
_G.print = realPrint
assert(#printed == 3, "each command answers in chat, got " .. #printed)

print("ok")
