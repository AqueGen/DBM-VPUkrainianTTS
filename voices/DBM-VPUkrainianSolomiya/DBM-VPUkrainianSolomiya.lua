local PATH = "Interface\\AddOns\\DBM-VPUkrainianSolomiya\\events\\"

if DBM then
	DBM:AddVictorySound("Ukrainian Solomiya: Victory", PATH .. "victory.ogg", 2)
	DBM:AddDefeatSound("Ukrainian Solomiya: Wipe", PATH .. "wipe.ogg", 2)
end

local LSM = LibStub and LibStub("LibSharedMedia-3.0", true)
if LSM then
	LSM:Register("sound", "Ukrainian Solomiya: Pull", PATH .. "pull.ogg")
	LSM:Register("sound", "Ukrainian Solomiya: Engage", PATH .. "engage.ogg")
end
