namespace FilterPrinterMod
{
    internal static class Tooltips
    {
        internal static void OnTooltip(RichTextBuilder builder, GameItem item)
        {
            if (builder == null || item == null)
            {
                return;
            }
            if (Cartridges.IsCartridge(item))
            {
                string target = Cartridges.TargetOf(item);
                if (!string.IsNullOrEmpty(target))
                {
                    builder.AddLine(Text.Get("cartridge.target_line", RetentionTargets.DisplayName(target)), true, RenderHandler.ColorPalette.LightCyan);
                }
                return;
            }
            if (item.identifier == FilterPrinterMachine.ItemId)
            {
                builder.AddLine(Text.Get("printer.tooltip.selected", RetentionTargets.DisplayName(FilterPrinterMachine.ReadSelected(item))), true, RenderHandler.ColorPalette.LightCyan);
                builder.AddLine(Text.Get("printer.tooltip.power", FilterPrinterMod.PrintPowerCost), true, RenderHandler.ColorPalette.LightGray);
                builder.AddLine(Text.Get("printer.tooltip.hint"), true, RenderHandler.ColorPalette.LightGray);
            }
        }
    }
}
