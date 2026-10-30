-- Run: lua tests/whats_new.lua   (Lua 5.1, from the pack root)
local handlers, timers, shown = {}, {}, 0
_G.CreateFrame = function()
	local frame = {}
	function frame:RegisterEvent(event) handlers[event] = self end
	function frame:UnregisterAllEvents() end
	function frame:SetScript(_, fn) self.handler = fn end
	return frame
end
_G.C_Timer = {After = function(_, fn) timers[#timers + 1] = fn end}
_G.SlashCmdList = {}
_G.hooksecurefunc = function(t, name, fn)
	local orig = t[name]
	t[name] = function(...) orig(...) fn(...) end
end

_G.DBM = {
	VoiceVersions = {UkrainianTTS = 20, UkrainianAlex = 20},
	Options = {
		ChosenVoicePack2 = "UkrainianTTS", PullVoice = "VP: UkrainianTTS", CountdownVoice = "Corsica",
		CountdownVoice2 = "VP: UkrainianAlex",
		EventSoundWipe = "Interface\\AddOns\\DBM-VPUkrainianTTS\\events\\wipe.ogg", EventSoundPullTimer = "None",
	},
	CheckVoicePackVersion = function() end,
	BuildVoiceCountdownCache = function() end,
}

local ns = {}
for _, file in ipairs({"text/Engine.lua", "VoiceSync.lua", "WhatsNew.lua"}) do
	assert(loadfile(file), "cannot load " .. file)("DBM-VPUkrainianTTS", ns)
end
ns.ShowWhatsNew = function() shown = shown + 1 end -- the window itself needs the game

local function login()
	handlers.PLAYER_LOGIN.handler(handlers.PLAYER_LOGIN)
	for _, fn in ipairs(timers) do fn() end
	timers = {}
end

login()
assert(shown == 1, "first login after the update shows the window")
login()
assert(shown == 1, "the window is shown once per notes version")

assert(ns.VoiceState("UkrainianTTS") == "chosen")
assert(ns.VoiceState("UkrainianAlex") == "ready")
assert(ns.VoiceState("UkrainianEvgeniy") == "off", "a pack switched off in the addon list cannot be picked")

local o = DBM.Options
-- DBM checks every pack at login and again 10 s later; that must not undo a mix the player chose.
for _ = 1, 2 do
	DBM:CheckVoicePackVersion("UkrainianTTS")
	DBM:CheckVoicePackVersion("UkrainianAlex")
end
assert(o.CountdownVoice2 == "VP: UkrainianAlex", "a login check must not move anything")
assert(o.PullVoice == "VP: UkrainianTTS")

ns.ChooseVoice("UkrainianAlex")
assert(o.ChosenVoicePack2 == "UkrainianAlex")
assert(o.PullVoice == "VP: UkrainianAlex", "our countdown follows the voice")
assert(o.CountdownVoice == "Corsica", "a countdown the player took from elsewhere stays")
assert(o.EventSoundWipe == "Interface\\AddOns\\DBM-VPUkrainianAlex\\events\\wipe.ogg")
assert(o.EventSoundPullTimer == "None", "a sound the player switched off stays off")

-- From a foreign pack to ours is a change too.
o.ChosenVoicePack2 = "VEM"
DBM:CheckVoicePackVersion("VEM")
ns.ChooseVoice("UkrainianTTS")
assert(o.PullVoice == "VP: UkrainianTTS" and o.CountdownVoice2 == "VP: UkrainianTTS")

local function read(path)
	local f = assert(io.open(path, "rb"), "missing " .. path)
	local text = f:read("*a")
	f:close()
	return text
end
local shared = read("VoiceSync.lua")
for _, voice in ipairs(ns.VOICES) do
	if voice[1] ~= "UkrainianTTS" then
		local folder = "voices/DBM-VP" .. voice[1] .. "/"
		assert(read(folder .. "VoiceSync.lua") == shared, folder .. "VoiceSync.lua must stay an identical copy")
		assert(read(folder .. "DBM-VP" .. voice[1] .. "_Mainline.toc"):find("ShortName: " .. voice[1], 1, true))
	end
end
print("whats_new ok")
