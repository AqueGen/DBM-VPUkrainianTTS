local _, ns = ...

local RELOAD_NOTE = "Зміна діє після перезавантаження інтерфейсу (/reload)."

local function Register()
	local db = ns.DB()
	local category = Settings.RegisterVerticalLayoutCategory("DBM Voice Ukrainian")

	local actionText = Settings.RegisterAddOnSetting(category, "DBM_VP_UKRAINIANTTS_ACTION_TEXT",
		"actionText", db, Settings.VarType.Boolean, "Текстові підказки", false)
	Settings.CreateCheckbox(category, actionText,
		"Замінює назву здібності в попередженнях DBM на дію тим самим текстом, який промовляє озвучка. "
		.. RELOAD_NOTE)

	local showTags = Settings.RegisterAddOnSetting(category, "DBM_VP_UKRAINIANTTS_SHOW_TAGS",
		"showTags", db, Settings.VarType.Boolean, "Показувати теги", true)
	Settings.CreateCheckbox(category, showTags,
		"Додає перед фразою тег дії: АОЕ, ТАНК, ЗБИЙ, РОЗВІЙ, ПОГЛИНИ, АДДИ, ВІДІЙДИ, УХИЛЯЙСЯ, "
		.. "РОЗІЙДІТЬСЯ, ЗБЕРІТЬСЯ. " .. RELOAD_NOTE)

	Settings.RegisterAddOnCategory(category)
end

local frame = CreateFrame("Frame")
frame:RegisterEvent("ADDON_LOADED")
frame:SetScript("OnEvent", function(self, _, addon)
	if addon ~= "DBM-VPUkrainianTTS" then return end
	self:UnregisterAllEvents()
	Register()
end)
