-- Registers the event sounds that DBM does not discover from the TOC metadata.
--
-- Alert phrases and the countdown are resolved by DBM-Core from the addon folder
-- name, so they need no code. Victory and wipe go through the DBM sound API, while
-- the "pull timer start" and "encounter engage" dropdowns are fed by LibSharedMedia
-- (see DBM-GUI/modules/options/alerts/EventSounds.lua).
local PATH = "Interface\\AddOns\\DBM-VPUkrainianTTS\\events\\"

if DBM then
	DBM:AddVictorySound("Ukrainian: Victory", PATH .. "victory.ogg", 2)
	DBM:AddDefeatSound("Ukrainian: Wipe", PATH .. "wipe.ogg", 2)
end

local LSM = LibStub and LibStub("LibSharedMedia-3.0", true)
if LSM then
	LSM:Register("sound", "Ukrainian: Pull", PATH .. "pull.ogg")
	LSM:Register("sound", "Ukrainian: Engage", PATH .. "engage.ogg")
end
