using System;
using HarmonyLib;
using UnityEngine;

namespace ScavProbe
{
    [HarmonyPatch(typeof(DumpingGroundLocation), "BuildPanel")]
    internal static class BuildPanelPatch
    {
        private static void Postfix(CustomUIBuilder builder)
        {
            try
            {
                builder.AddButton("M0 探针", () => ProbeWindow.Open());
            }
            catch (Exception e)
            {
                Debug.LogException(e);
            }
        }
    }

    [HarmonyPatch(typeof(DumpingGroundLocation), "OnScavenge")]
    internal static class OnScavengePatch
    {
        private static bool Prefix()
        {
            try
            {
                return !ProbeWindow.Open();
            }
            catch (Exception e)
            {
                Debug.LogException(e);
                return true;
            }
        }
    }

    [HarmonyPatch(typeof(MapUIManager), "ScavengeButtonClick")]
    internal static class ScavengeButtonPatch
    {
        private static bool Prefix()
        {
            try
            {
                return !ProbeWindow.Open();
            }
            catch (Exception e)
            {
                Debug.LogException(e);
                return true;
            }
        }
    }
}
