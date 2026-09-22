-- Run: lua tests/action_text.lua   (Lua 5.1, from the pack root)
local files = {"text/Phrases.lua", "text/Tags.lua", "text/Actions.lua", "text/Engine.lua"}

local handler
_G.CreateFrame = function()
	return {
		RegisterEvent = function() end,
		UnregisterAllEvents = function() end,
		SetScript = function(_, _, fn) handler = fn end,
	}
end

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
end

ns.DB().actionText = false
handler(nil, "PLAYER_LOGIN")
assert(next(renames) == nil, "nothing may be renamed while the feature is off")

ns.DB().actionText = true
handler(nil, "PLAYER_LOGIN")
assert(renames[1286860] == "АОЕ | Скоро шкода по площі", tostring(renames[1286860]))
assert(renames[1298367] == "ТАНК | Прожми захист", tostring(renames[1298367]))
assert(renames[1286895] == "ВІДІЙДИ | Бомба на тобі, відбіжи від групи", tostring(renames[1286895]))
assert(renames[2001] == "РОЗІЙДІТЬСЯ | Розійдіться на 5 метрів", tostring(renames[2001]))
assert(renames[1295905] == "ЗБЕРІТЬСЯ | Зберіться, ділимо шкоду", tostring(renames[1295905]))
assert(renames[2002] == "Артилерія", tostring(renames[2002]))
assert(renames[999] == nil, "an unknown voice key must be left alone")
assert(renames[111] == nil, "a warning without a voice key must be left alone")

ns.DB().showTags = false
assert(ns.TextFor("aesoon") == "Скоро шкода по площі", ns.TextFor("aesoon"))
ns.DB().showTags = true

renames = {}
handler(nil, "ADDON_LOADED", "Details")
assert(next(renames) == nil, "a non-DBM addon must not trigger a pass")
handler(nil, "ADDON_LOADED", "DBM-Party-Midnight")
assert(renames[1286860] == "АОЕ | Скоро шкода по площі")

print("ok")
