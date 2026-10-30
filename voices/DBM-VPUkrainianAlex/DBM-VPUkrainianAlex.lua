local PATH = "Interface\\AddOns\\DBM-VPUkrainianAlex\\events\\"

if DBM then
	DBM:AddVictorySound("Ukrainian Alex: Victory", PATH .. "victory.ogg", 2)
	DBM:AddDefeatSound("Ukrainian Alex: Wipe", PATH .. "wipe.ogg", 2)
end

local LSM = LibStub and LibStub("LibSharedMedia-3.0", true)
if LSM then
	LSM:Register("sound", "Ukrainian Alex: Pull", PATH .. "pull.ogg")
	LSM:Register("sound", "Ukrainian Alex: Engage", PATH .. "engage.ogg")
end
