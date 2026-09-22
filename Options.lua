local _, ns = ...

local ACTION_TEXT = "DBM_VP_UKRAINIANTTS_ACTION_TEXT"
local SHOW_TAGS = "DBM_VP_UKRAINIANTTS_SHOW_TAGS"

StaticPopupDialogs["DBM_VP_UKRAINIANTTS_RELOAD"] = {
	text = "Зміна набуде чинності після перезавантаження інтерфейсу.",
	button1 = "Перезавантажити",
	button2 = "Пізніше",
	OnAccept = ReloadUI,
	timeout = 0,
	whileDead = true,
	hideOnEscape = true,
}

local function OnChanged(setting, value)
	if setting:GetVariable() == ACTION_TEXT and value and not ns.applied then
		ns.ApplyRenames()
		if ns.applied then return end
	end
	StaticPopup_Show("DBM_VP_UKRAINIANTTS_RELOAD")
end

local function Register()
	local db = ns.DB()
	local category = Settings.RegisterVerticalLayoutCategory("DBM Voice Ukrainian")

	local actionText = Settings.RegisterAddOnSetting(category, ACTION_TEXT,
		"actionText", db, Settings.VarType.Boolean, "Текстові підказки", false)
	Settings.CreateCheckbox(category, actionText,
		"Замінює назву здібності в попередженнях DBM на дію тим самим текстом, який промовляє озвучка.")

	local showTags = Settings.RegisterAddOnSetting(category, SHOW_TAGS,
		"showTags", db, Settings.VarType.Boolean, "Показувати теги", true)
	Settings.CreateCheckbox(category, showTags,
		"Додає перед фразою тег дії: АОЕ, ТАНК, ЗБИЙ, РОЗВІЙ, ПОГЛИНИ, АДДИ, ВІДІЙДИ, УХИЛЯЙСЯ, "
		.. "РОЗІЙДІТЬСЯ, ЗБЕРІТЬСЯ.")

	Settings.SetOnValueChangedCallback(ACTION_TEXT, OnChanged)
	Settings.SetOnValueChangedCallback(SHOW_TAGS, OnChanged)
	Settings.RegisterAddOnCategory(category)
end

local frame = CreateFrame("Frame")
frame:RegisterEvent("ADDON_LOADED")
frame:SetScript("OnEvent", function(self, _, addon)
	if addon ~= "DBM-VPUkrainianTTS" then return end
	self:UnregisterAllEvents()
	Register()
end)
