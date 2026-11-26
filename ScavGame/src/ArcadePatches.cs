using System;
using HarmonyLib;
using UnityEngine;

namespace ScavArcade
{
    [HarmonyPatch(typeof(DumpingGroundLocation), "BuildPanel")]
    internal static class BuildPanelPatch
    {
        private static void Postfix(CustomUIBuilder builder)
        {
            try
            {
                builder.AddButton(TextBank.Get("ui.enter"), () => ArcadeWindow.Open());
            }
            catch (Exception e)
            {
                Debug.LogException(e);
            }
        }
    }

    [HarmonyPatch(typeof(ItemSpawner), "Spawn")]
    internal static class ItemSpawnPatch
    {
        private static void Postfix(GameItem __result)
        {
            try
            {
                ArcadeWindow.OnItemSpawned(__result);
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
                return !ArcadeWindow.Open();
            }
            catch (Exception e)
            {
                Debug.LogException(e);
                return true;
            }
        }
    }

    [HarmonyPatch(typeof(MapUIManager), "Return")]
    internal static class ReturnPatch
    {
        private static void Prefix()
        {
            try
            {
                ArcadeWindow.Close();
            }
            catch (Exception e)
            {
                Debug.LogException(e);
            }
        }
    }

    [HarmonyPatch(typeof(MapUIManager), "ReturnNow")]
    internal static class ReturnNowPatch
    {
        private static void Prefix()
        {
            try
            {
                ArcadeWindow.Close();
            }
            catch (Exception e)
            {
                Debug.LogException(e);
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
                return !ArcadeWindow.Open();
            }
            catch (Exception e)
            {
                Debug.LogException(e);
                return true;
            }
        }
    }
}
