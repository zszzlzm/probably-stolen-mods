using System.Collections.Generic;

namespace FilterPrinterMod
{
    internal static class FilterPrinterMachine
    {
        internal const string ItemId = "fp_printer";
        internal const string MachineSprite = "fp_printer";
        internal const string SelectedTag = "FP_SELECTED_TARGET_TAG";
        private const int RowsPerColumn = 5;

        internal static GameItem Create()
        {
            GameSlotInventory battery = new GameSlotInventory();
            GameSlotInventory output = new GameSlotInventory();
            output.mayInventoryAddItemFunc = (GameItem item, GameInventory _) => item != null && Cartridges.IsCartridge(item);

            GameItem machine = null;
            List<MachineryRadioButton> allButtons = new List<MachineryRadioButton>();
            List<string> allIds = new List<string>();
            MachineryTabs tabs = new MachineryTabs();

            foreach (RetentionCategory category in RetentionTargets.BuildCategories())
            {
                MachineryRadioGroup group = new MachineryRadioGroup();
                MachineryStack left = new MachineryStack(vertical: true, gap: 6);
                MachineryStack right = new MachineryStack(vertical: true, gap: 6);
                for (int i = 0; i < category.Liquids.Count; i++)
                {
                    string liquidId = category.Liquids[i];
                    MachineryRadioButton radio = new MachineryRadioButton(RetentionTargets.DisplayName(liquidId), false);
                    group.Add(radio);
                    allButtons.Add(radio);
                    allIds.Add(liquidId);
                    if (i < RowsPerColumn)
                    {
                        left.Add(radio);
                    }
                    else
                    {
                        right.Add(radio);
                    }
                }
                MachineryStack columns = MachineryStack.Horizontal(left, right);
                columns.gap = 14;
                columns.Validate();
                tabs.AddTab(Text.Get(category.CaptionKey), columns);
                group.onChanged = (int index) =>
                {
                    if (index < 0 || index >= category.Liquids.Count)
                    {
                        return;
                    }
                    string liquidId = category.Liquids[index];
                    SetSelected(machine, liquidId);
                    ApplySelection(allButtons, allIds, liquidId);
                };
            }

            MachineryButton print = new MachineryButton(Text.Get("printer.btn.print"));
            MachineryText status = MachineryText.Status(Text.Get("printer.status.label"), "");
            MachineryStack control = MachineryStack.Vertical(tabs, status, print);
            control.gap = 8;
            control.Validate();

            PixelWindow window = MachineHelper.CreateMachineryWindow(
                true,
                MachineHelper.PowerPanel(battery),
                MachineHelper.Panel(Text.Get("printer.panel.output"), output, "output"),
                MachineHelper.Panel(Text.Get("printer.panel.control"), control, "control"));

            machine = ItemDirectory.CreateEmptyItem(ItemId)
                .SetContentWindow(window);
            // Dedicated sprite: the machine must not share the vanilla 3D printer's art,
            // otherwise a player running both cannot tell them apart. Ships as
            // mod/Textures/Items/fp_printer.png (48x48 = 3x3 cells); the vanilla sprite
            // stays as a fallback for folders that somehow lack the PNG.
            machine.SetSpriteAndShapeFromMod(FilterPrinterMod.ModId, MachineSprite);
            if (string.IsNullOrEmpty(machine.spritePath))
            {
                machine.SetSpriteAndShape("Items/items_tool2", "printer_off");
            }
            machine.name = Text.Get("printer.name");
            machine.shortDescription = Text.Get("printer.desc");
            machine.flavorText = Text.Get("printer.flavor");
            machine.unitValue = 1200L;
            machine.EnableTag("CONTAINER_TAG");
            machine.EnableTag("manufacture");
            machine.EnableTag("STANDARD_MACHINE_TAG");
            machine.EnableTag("IMPORTANT_TAG");
            machine.SetGameItemType("MACHINE");
            MachineHelper.SetupBatterySlot(battery, machine);
            battery.onSlotAddItemFunc += (GameItem _, GameInventory _, SlotMarker _) => RefreshStatus(status, battery);
            battery.onSlotRemoveItemFunc += (GameItem _, GameInventory _, SlotMarker _) => RefreshStatus(status, battery);

            print.SetCallback(() => TryPrint(machine, output, battery, status));
            machine.onLoaded = (GameItem loaded) =>
            {
                RepointSprite(loaded);
                ApplySelection(allButtons, allIds, ReadSelected(loaded));
                RefreshStatus(status, battery);
            };
            ApplySelection(allButtons, allIds, ReadSelected(machine));
            RefreshStatus(status, battery);

            machine.contentWindow.Validate();
            machine.Validate();
            AudioHelper.InitSmallMachine(machine);
            return machine;
        }

        /// <summary>
        /// Machines saved by older versions stored the vanilla 3D printer sprite
        /// ("Items/items_tool2" / "printer_off") per item, so loading them kept the old
        /// look. Re-point them at the mod sprite once, on load.
        /// </summary>
        private static void RepointSprite(GameItem item)
        {
            if (item == null || item.useSpriteFromMod)
            {
                return;
            }
            item.SetSpriteAndShapeFromMod(FilterPrinterMod.ModId, MachineSprite);
            if (string.IsNullOrEmpty(item.spritePath))
            {
                item.SetSpriteAndShape("Items/items_tool2", "printer_off");
            }
        }

        private static void ApplySelection(List<MachineryRadioButton> buttons, List<string> ids, string target)
        {
            for (int i = 0; i < buttons.Count; i++)
            {
                buttons[i].SetOn(ids[i] == target, notify: false);
            }
        }

        internal static string ReadSelected(GameItem machine)
        {
            if (machine == null)
            {
                return RetentionTargets.ContaminantIds[0];
            }
            TagState state = machine.GetTagReadonly(SelectedTag);
            string raw = state == null ? null : state.GetString();
            return string.IsNullOrEmpty(raw) ? RetentionTargets.ContaminantIds[0] : raw;
        }

        private static void SetSelected(GameItem machine, string target)
        {
            if (machine == null)
            {
                return;
            }
            machine.ModifyTag(SelectedTag, (TagState state) =>
            {
                state.Enable().SetString(target);
            });
        }

        private static int EnergyOf(GameItem cell)
        {
            if (cell == null)
            {
                return 0;
            }
            return cell.GetTagReadonly("power_source_item_energy").GetInt();
        }

        private static int CreditCostOf(GameItem converter, int energy)
        {
            if (converter == null)
            {
                return 0;
            }
            return CurrentConverterHelper.ToCredits(energy, CurrentConverterHelper.GetRate(converter));
        }

        private static void RefreshStatus(MachineryText status, GameSlotInventory battery)
        {
            if (status == null)
            {
                return;
            }
            string label = Text.Get("printer.status.label");
            GameItem cell = battery != null ? battery.childItem : null;
            int cost = FilterPrinterMod.PrintPowerCost;
            if (cell == null)
            {
                status.SetStatus(label, Text.Get("printer.status.empty", cost));
                return;
            }
            if (CurrentConverterHelper.IsCurrentConverter(cell))
            {
                if (!CurrentConverterHelper.IsOn(cell))
                {
                    status.SetStatus(label, Text.Get("printer.status.converter_off", cost));
                }
                else
                {
                    status.SetStatus(label, Text.Get("printer.status.converter", CrediCostSafe(cell, cost), cost));
                }
                return;
            }
            if (HypertechBatteryHelper.IsHypertechBattery(cell))
            {
                status.SetStatus(label, Text.Get("printer.status.hypertech", HypertechBatteryHelper.GetOutput(cell), cost));
                return;
            }
            status.SetStatus(label, Text.Get("printer.status.power", EnergyOf(cell), cost));
        }

        private static int CrediCostSafe(GameItem converter, int energy)
        {
            try
            {
                return CreditCostOf(converter, energy);
            }
            catch
            {
                return 0;
            }
        }

        private static GameSlotInventory ResolveBatterySlot(GameItem machine, GameSlotInventory fallback)
        {
            try
            {
                GameSlotInventory slot = MachineHelper.GetBatterySlot(machine);
                if (slot != null)
                {
                    return slot;
                }
            }
            catch
            {
            }
            return fallback;
        }

        private static int CashOf()
        {
            try
            {
                return PlayerStore.Instance != null ? PlayerStore.Instance.playerCash : 0;
            }
            catch
            {
                return 0;
            }
        }

        private static string PowerProblem(GameItem cell, int cost, out object[] args)
        {
            args = null;
            if (CurrentConverterHelper.IsCurrentConverter(cell))
            {
                if (!CurrentConverterHelper.IsOn(cell))
                {
                    args = new object[] { cost };
                    return "printer.msg.converter_off";
                }
                if (CurrentConverterHelper.IsBlackedOut())
                {
                    args = new object[] { cost };
                    return "printer.msg.blackout";
                }
                int credits = CrediCostSafe(cell, cost);
                if (!CanPay(credits))
                {
                    args = new object[] { credits };
                    return "printer.msg.credits";
                }
            }
            else if (HypertechBatteryHelper.IsHypertechBattery(cell))
            {
                int output = HypertechBatteryHelper.GetOutput(cell);
                if (output < cost)
                {
                    args = new object[] { output, cost };
                    return "printer.msg.hypertech";
                }
            }
            else if (EnergyOf(cell) < cost)
            {
                args = new object[] { cost, EnergyOf(cell) };
                return "printer.msg.no_power";
            }
            bool ok;
            try
            {
                ok = PowerHelper.CanDrawPowerSource(cell, cost);
            }
            catch (System.Exception e)
            {
                FilterPrinterMod.LogInfo("CanDrawPowerSource threw: " + e.GetType().Name + ": " + e.Message);
                ok = false;
            }
            if (!ok)
            {
                args = new object[] { cost, EnergyOf(cell) };
                return "printer.msg.no_power_generic";
            }
            return null;
        }

        private static bool CanPay(int credits)
        {
            try
            {
                return PlayerStore.Instance != null && PlayerStore.Instance.CanPay(credits);
            }
            catch
            {
                return false;
            }
        }

        private static void TryFreeOutput(GameSlotInventory output, GameItem stuck)
        {
            if (output == null || stuck == null)
            {
                return;
            }
            try
            {
                if (!output.Expel(stuck))
                {
                    FilterPrinterMod.LogInfo("Could not expel '" + stuck.identifier + "' from the output slot");
                    return;
                }
                GraphUtils.EmporiumTryAdd(EmporiumEntry.Instance.invElement, stuck);
            }
            catch (System.Exception e)
            {
                FilterPrinterMod.LogInfo("Freeing the output slot threw: " + e.GetType().Name + ": " + e.Message);
            }
        }

        private static void TryPrint(GameItem machine, GameSlotInventory output, GameSlotInventory battery, MachineryText status)
        {
            if (machine == null || output == null)
            {
                return;
            }
            int cost = FilterPrinterMod.PrintPowerCost;
            if (output.childItem != null)
            {
                GameItem stuck = output.childItem;
                string stuckId = stuck != null ? stuck.identifier : "null";
                bool stuckOwned = stuck != null && GeneralHelper.IsItemOwned(stuck);
                FilterPrinterMod.LogInfo("Output slot busy with '" + stuckId + "' owned=" + stuckOwned + "; moving it to the player inventory");
                TryFreeOutput(output, stuck);
                if (output.childItem != null)
                {
                    FilterPrinterMod.LogInfo("Output slot is still busy after the attempt; print cancelled");
                    Warn("printer.msg.output_full");
                    return;
                }
            }
            GameSlotInventory slot = ResolveBatterySlot(machine, battery);
            GameItem cell = slot != null ? slot.childItem : null;
            if (cell == null)
            {
                FilterPrinterMod.LogInfo("Print refused: the battery slot is empty");
                Warn("printer.msg.no_battery", cost);
                RefreshStatus(status, slot);
                return;
            }
            object[] args;
            string problem = PowerProblem(cell, cost, out args);
            if (problem != null)
            {
                FilterPrinterMod.LogInfo("Print refused (" + problem + ") cost=" + cost + ", cell='" + cell.identifier + "', energy=" + EnergyOf(cell) + ", cash=" + CashOf());
                Warn(problem, args);
                RefreshStatus(status, slot);
                return;
            }
            string target = ReadSelected(machine);
            GameItem cartridge = DirectoryMaster.Item(Cartridges.ItemId(target));
            if (cartridge == null)
            {
                return;
            }
            bool fits = GraphUtils.CanAccept(output, cartridge);
            if (!fits)
            {
                FilterPrinterMod.LogInfo("Output slot refused the cartridge by shape/filter (shape " + cartridge.modifiedShape.globalWidth + "x" + cartridge.modifiedShape.globalHeight + ", owned=" + GeneralHelper.IsItemOwned(cartridge) + "); placing it directly");
            }
            int energyBefore = EnergyOf(cell);
            int cashBefore = CashOf();
            bool drawn = false;
            try
            {
                drawn = PowerHelper.DrawPowerSource(cell, cost);
            }
            catch (System.Exception e)
            {
                FilterPrinterMod.LogInfo("DrawPowerSource threw: " + e.GetType().Name + ": " + e.Message);
            }
            if (!drawn)
            {
                FilterPrinterMod.LogInfo("Draw failed after pre-check: cost=" + cost + ", cell='" + cell.identifier + "', energy=" + EnergyOf(cell) + ", cash=" + CashOf() + "; no cartridge made");
                GraphUtils.TryDestroyAll(new List<GameItem> { cartridge }, 1);
                Warn("printer.msg.no_power_generic", cost);
                RefreshStatus(status, slot);
                return;
            }
            bool placed;
            if (fits)
            {
                // TryAcceptAll 返回的是「没放进去的剩余数量」，0 才代表放置成功。
                int leftover = GraphUtils.TryAcceptAll(output, cartridge);
                placed = leftover == 0;
                if (!placed)
                {
                    FilterPrinterMod.LogInfo("Output slot accepted the cartridge only partially; leftover=" + leftover);
                }
            }
            else
            {
                try
                {
                    placed = output.UncheckedAccept(cartridge);
                }
                catch (System.Exception e)
                {
                    FilterPrinterMod.LogInfo("Direct placement threw: " + e.GetType().Name + ": " + e.Message);
                    placed = false;
                }
            }
            if (!placed)
            {
                FilterPrinterMod.LogInfo("Could not place the cartridge in the output slot; refunding");
                Refund(cell, energyBefore, cashBefore);
                GraphUtils.TryDestroyAll(new List<GameItem> { cartridge }, 1);
                Warn("printer.msg.output_full");
                RefreshStatus(status, slot);
                return;
            }
            int energyAfter = EnergyOf(cell);
            int cashAfter = CashOf();
            FilterPrinterMod.LogInfo(
                "Printed '" + target + "': cost=" + cost + ", drawn=" + drawn + ", fits=" + fits
                + ", energy " + energyBefore + "->" + energyAfter
                + ", cash " + cashBefore + "->" + cashAfter
                + ", cell='" + cell.identifier + "'");
            try
            {
                if (slot != null)
                {
                    slot.Validate();
                }
            }
            catch
            {
            }
            RefreshStatus(status, slot);
            AudioManager.Instance.Play3("module_insert");
        }

        private static void Refund(GameItem cell, int energyBefore, int cashBefore)
        {
            try
            {
                if (cell == null)
                {
                    return;
                }
                if (CurrentConverterHelper.IsCurrentConverter(cell))
                {
                    if (PlayerStore.Instance != null)
                    {
                        PlayerStore.Instance.playerCash = cashBefore;
                    }
                    return;
                }
                if (HypertechBatteryHelper.IsHypertechBattery(cell))
                {
                    return;
                }
                cell.ModifyTag("power_source_item_energy", (TagState state) =>
                {
                    state.Enable().SetInt(energyBefore);
                });
                PowerHelper.UpdateEnergyCreditSprite(cell);
            }
            catch (System.Exception e)
            {
                FilterPrinterMod.LogInfo("Refund failed: " + e.Message);
            }
        }

        private static void Warn(string locKey, params object[] args)
        {
            string message = Text.Get(locKey, args);
            FilterPrinterMod.LogInfo(message);
            if (GenericConfirmationUIManager.Instance != null)
            {
                GenericConfirmationUIManager.Instance.OpenPanelSingleButton(
                    message,
                    LocHelper.GetLocalizedMainMenu("confirm"),
                    () => GenericConfirmationUIManager.Instance.ClosePanel());
            }
        }
    }
}
