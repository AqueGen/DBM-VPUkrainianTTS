local _, ns = ...

-- Bump when NOTES change; every player then sees the window once more.
local NOTES_VERSION = 1
local NOTES = "Три нові голоси: Alex, Evgeniy і Solomiya. Послухайте їх і оберіть свій.\n"
	.. "Відлік і звуки подій, налаштовані на наш голос, перемикаються разом з ним."

ns.VOICES = {
	{"UkrainianTTS", "Polina", "жіночий"},
	{"UkrainianAlex", "Alex", "чоловічий", true},
	{"UkrainianEvgeniy", "Evgeniy", "чоловічий", true},
	{"UkrainianSolomiya", "Solomiya", "жіночий", true},
}
local PREVIEW = {{"kite", 1.5}, {"kickcast", 1.8}, {"count\\3", 1}, {"count\\2", 1}, {"count\\1", 1}}

local window, rows, playing

local function StopPreview()
	if not playing then return end
	if playing.timer then playing.timer:Cancel() end
	if playing.handle then StopSound(playing.handle) end
	playing = nil
end

function ns.VoiceState(short)
	if not (DBM and DBM.VoiceVersions[short]) then return "off" end
	return DBM.Options.ChosenVoicePack2 == short and "chosen" or "ready"
end

local function Refresh()
	if not (window and window:IsShown()) then return end
	for _, row in ipairs(rows) do
		local state = ns.VoiceState(row.short)
		row.listen:SetEnabled(state ~= "off")
		row.listen:SetText(playing and playing.short == row.short and "Стоп" or "Слухати")
		row.choose:SetShown(state == "ready")
		row.status:SetShown(state ~= "ready")
		row.status:SetText(state == "chosen" and "|cff7fd16aОбрано|r" or "|cff9a937eвимкнено в списку аддонів|r")
	end
end

local function Preview(short)
	local again = playing and playing.short == short
	StopPreview()
	if not again then
		local current = {short = short}
		playing = current
		local channel = DBM.Options.UseSoundChannel == "Dialog" and "Dialog" or "Master"
		local function Step(i)
			if playing ~= current then return end
			local clip = PREVIEW[i]
			if not clip then
				playing = nil
				Refresh()
				return
			end
			local _, handle = PlaySoundFile("Interface\\AddOns\\DBM-VP" .. short .. "\\" .. clip[1] .. ".ogg", channel)
			current.handle = handle
			current.timer = C_Timer.NewTimer(clip[2], function() Step(i + 1) end)
		end
		Step(1)
	end
	Refresh()
end

-- The same two calls DBM's own voice dropdown makes; VoiceSync.lua moves the countdowns and event sounds.
function ns.ChooseVoice(short)
	DBM.Options.ChosenVoicePack2 = short
	DBM:CheckVoicePackVersion(short)
	Refresh()
end

local function Button(parent, text, width, onClick)
	local button = CreateFrame("Button", nil, parent, "UIPanelButtonTemplate")
	button:SetSize(width, 22)
	button:SetText(text)
	button:SetScript("OnClick", onClick)
	return button
end

local function Build()
	window = CreateFrame("Frame", "DBMVPUkrainianWhatsNew", UIParent, "BasicFrameTemplateWithInset")
	window:SetSize(460, 320)
	window:SetPoint("CENTER")
	window:SetFrameStrata("DIALOG")
	window:SetMovable(true)
	window:EnableMouse(true)
	window:RegisterForDrag("LeftButton")
	window:SetScript("OnDragStart", window.StartMoving)
	window:SetScript("OnDragStop", window.StopMovingOrSizing)
	window:SetScript("OnHide", StopPreview)
	window.TitleText:SetText("Що нового - DBM Voice Ukrainian")
	tinsert(UISpecialFrames, window:GetName())

	local notes = window:CreateFontString(nil, "OVERLAY", "GameFontHighlight")
	notes:SetPoint("TOPLEFT", 18, -36)
	notes:SetPoint("TOPRIGHT", -18, -36)
	notes:SetJustifyH("LEFT")
	notes:SetText(NOTES)

	rows = {}
	local anchor = notes
	for _, voice in ipairs(ns.VOICES) do
		local row = CreateFrame("Frame", nil, window)
		row:SetHeight(36)
		row:SetPoint("TOPLEFT", anchor, "BOTTOMLEFT", 0, -10)
		row:SetPoint("RIGHT", window, "RIGHT", -18, 0)
		row.short = voice[1]

		local name = row:CreateFontString(nil, "OVERLAY", "GameFontNormal")
		name:SetPoint("LEFT")
		name:SetJustifyH("LEFT")
		name:SetText(voice[2] .. (voice[4] and "  |cffffd100нове|r" or "") .. "\n|cff9a937e" .. voice[3] .. "|r")

		row.choose = Button(row, "Обрати", 90, function() ns.ChooseVoice(row.short) end)
		row.choose:SetPoint("RIGHT")
		row.status = row:CreateFontString(nil, "OVERLAY", "GameFontNormalSmall")
		row.status:SetPoint("RIGHT", row.choose, "RIGHT")
		row.listen = Button(row, "Слухати", 90, function() Preview(row.short) end)
		row.listen:SetPoint("RIGHT", row.choose, "LEFT", -8, 0)

		rows[#rows + 1] = row
		anchor = row
	end

	local dbm = Button(window, "Налаштування голосу в DBM", 210, function()
		window:Hide()
		DBM:LoadGUI()
	end)
	dbm:SetPoint("BOTTOMLEFT", 16, 14)
	local close = Button(window, "Закрити", 100, function() window:Hide() end)
	close:SetPoint("BOTTOMRIGHT", -16, 14)
end

function ns.ShowWhatsNew()
	if not window then Build() end
	window:Show()
	Refresh()
end

SLASH_DBMVPUKRAINIAN1 = "/dbmua"
SlashCmdList.DBMVPUKRAINIAN = ns.ShowWhatsNew

local frame = CreateFrame("Frame")
frame:RegisterEvent("PLAYER_LOGIN")
frame:SetScript("OnEvent", function(self)
	self:UnregisterAllEvents()
	-- DBM registers the voice packs a moment after login.
	C_Timer.After(3, function()
		local db = ns.DB()
		if db.whatsNewSeen == NOTES_VERSION or not DBM then return end
		db.whatsNewSeen = NOTES_VERSION
		ns.ShowWhatsNew()
	end)
end)
