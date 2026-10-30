local PATH = "Interface\\AddOns\\DBM-VPUkrainianEvgeniy\\events\\"

if DBM then
	DBM:AddVictorySound("Ukrainian Evgeniy: Victory", PATH .. "victory.ogg", 2)
	DBM:AddDefeatSound("Ukrainian Evgeniy: Wipe", PATH .. "wipe.ogg", 2)
end

local LSM = LibStub and LibStub("LibSharedMedia-3.0", true)
if LSM then
	LSM:Register("sound", "Ukrainian Evgeniy: Pull", PATH .. "pull.ogg")
	LSM:Register("sound", "Ukrainian Evgeniy: Engage", PATH .. "engage.ogg")
end
