local _, ns = ...

local ACTION_TEXT = "DBM_VP_UKRAINIANTTS_ACTION_TEXT"

StaticPopupDialogs["DBM_VP_UKRAINIANTTS_RELOAD"] = {
	text = "Зміна набуде чинності після перезавантаження інтерфейсу.",
	button1 = "Перезавантажити",
	button2 = "Пізніше",
	OnAccept = ReloadUI,
	timeout = 0,
	whileDead = true,
	hideOnEscape = true,
}

local function OnChanged(_, _, value)
	if value then
		ns.ApplyRenames()
		if not ns.applied then
			print(ns.PREFIX .. ns.L.PENDING)
		elseif not ns.WarningsShowRenames() then
			print(ns.PREFIX .. ns.L.DBM_RENAMES_OFF)
		end
	elseif ns.applied then
		StaticPopup_Show("DBM_VP_UKRAINIANTTS_RELOAD")
	end
end

local function Register()
	local category = Settings.RegisterVerticalLayoutCategory("DBM Voice Ukrainian")
	local setting = Settings.RegisterAddOnSetting(category, ACTION_TEXT, "actionText", ns.DB(),
		Settings.VarType.Boolean, "Текстові підказки", false)
	Settings.CreateCheckbox(category, setting,
		"Замінює назву здібності в попередженнях DBM на дію тим самим текстом, який промовляє озвучка: "
		.. "\"АОЕ | Скоро шкода по площі\" замість \"Rage of the Shackled\".")
	Settings.SetOnValueChangedCallback(ACTION_TEXT, OnChanged)
	Settings.RegisterAddOnCategory(category)
end

local frame = CreateFrame("Frame")
frame:RegisterEvent("ADDON_LOADED")
frame:SetScript("OnEvent", function(self, _, addon)
	if addon ~= "DBM-VPUkrainianTTS" then return end
	self:UnregisterAllEvents()
	Register()
end)
