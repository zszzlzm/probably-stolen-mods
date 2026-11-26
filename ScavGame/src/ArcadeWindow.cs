using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

namespace ScavArcade
{
    internal static class ArcadeWindow
    {
        private const string WindowId = "scav_arcade";
        private const int Columns = 6;
        private const int Rows = 4;
        private const int CellCount = Columns * Rows;

        private const int KindInjured = 0;
        private const int KindEmpty = 1;
        private const int KindBase = 2;
        private const int KindSealed = 4;
        private const int KindMachine = 5;

        private sealed class CellData
        {
            public int kind;
            public bool major;
            public bool extra;
            public int baseRolls;
            public List<string> dismantleTools;
            public List<GameItem> items;
            public GameItem backpack;
            public string baseTable;
        }

        private static CustomUIWindow window;
        private static CustomUIElement statusLabel;
        private static CustomUIElement clueLabel;
        private static CustomUIElement logLabel;
        private static CustomUIElement[] cellElements;
        private static CellData[] cells;
        private static CellData rollingCell;
        private static bool expectingBaseSpawn;
        private static bool autoTestActive;
        private static int autoTestStep;
        private static float autoTestWait;
        private static int autoTestPass;
        private static int autoTestFail;
        private static string autoTestReportPath;
        private static readonly List<string> autoTestLines = new List<string>();
        private static bool boardOpened;
        private static bool[] used;
        private static bool[] marked;
        private static bool[] revealed;
        private static bool[] clued;
        private static int[] clueSource;
        private static string[] clueText;
        private static Color[] cellBaseColor;
        private static Color[] cellBaseText;
        private static int lastClick = -1;
        private static readonly List<string> lines = new List<string>();
        private static readonly System.Random rng = new System.Random();
        private static readonly string[] SealedItemTypes =
        {
            "MATERIAL", "BASIC_MATERIAL", "MEDICAL", "MEDICAL_TOOL", "ORGAN",
            "HOUSEHOLD_GOOD", "FOOD", "PROCESSED_FOOD", "BREVAGE", "ALCOHOL",
            "TOOL", "WEAPON", "MELEE_WEAPON", "FIREARM"
        };

        private static int attemptsLeft;
        private static int foundCount;
        private static bool ended;
        private static bool paused;
        private static GameObject pulseObject;
        private static bool hasCrowbar;
        private static bool hasMagnifier;
        private static bool hasFlashlight;
        private static int lightCharges;
        private static int inspectCharges;
        private static bool lightMode;
        private static bool inspectMode;
        private static CustomUIElement lightButton;
        private static CustomUIElement inspectButton;
        private static readonly Dictionary<string, int> lastPick = new Dictionary<string, int>();

        internal static void OnArrive()
        {
            attemptsLeft = 0;
            foundCount = 0;
            ended = false;
            lightMode = false;
            inspectMode = false;
            paused = false;
            boardOpened = false;
            cells = null;
            used = null;
            marked = null;
            revealed = null;
            clued = null;
            clueSource = null;
            clueText = null;
            lastClick = -1;
            lines.Clear();
            lastPick.Clear();
            hasCrowbar = EmporiumEntry.Instance != null && EmporiumEntry.Instance.IsAfterhourHaveOwnedItems("crowbar");
            hasMagnifier = EmporiumEntry.Instance != null && EmporiumEntry.Instance.IsAfterhourHaveOwnedItems("magnifier");
            hasFlashlight = EmporiumEntry.Instance != null && EmporiumEntry.Instance.IsAfterhourHaveOwnedItems("flashlight");
            lightCharges = hasFlashlight ? 3 : 0;
            inspectCharges = hasMagnifier ? 1 : 0;
            if (ScavHelper.CanScavenge())
            {
                try
                {
                    GenerateBoard();
                }
                catch (Exception e)
                {
                    Debug.LogException(e);
                    cells = null;
                }
            }
            MaybeStartAutoTest();
        }

        internal static void OnLootRolled(LootRollContext context)
        {
            if (rollingCell != null && context != null)
            {
                rollingCell.baseRolls++;
                expectingBaseSpawn = true;
                if (rollingCell.baseTable == null)
                {
                    rollingCell.baseTable = context.tableId;
                }
            }
        }

        internal static void OnItemSpawned(GameItem item)
        {
            if (rollingCell == null)
            {
                return;
            }
            if (expectingBaseSpawn)
            {
                expectingBaseSpawn = false;
                return;
            }
            if (item == null)
            {
                return;
            }
            string tool = null;
            if (item.identifier == "nuts_metal" && Carried("screwdriver"))
            {
                tool = "screwdriver";
            }
            else if (item.identifier == "wire" && Carried("wire_cutter"))
            {
                tool = "wire_cutter";
            }
            else if (item.identifier == "scrap_metal" && Carried("welder"))
            {
                tool = "welder";
            }
            if (tool == null)
            {
                return;
            }
            if (rollingCell.dismantleTools == null)
            {
                rollingCell.dismantleTools = new List<string>();
            }
            if (!rollingCell.dismantleTools.Contains(tool))
            {
                rollingCell.dismantleTools.Add(tool);
            }
            Debug.Log("[ScavArcade] dismantle " + tool + " item=" + item.identifier);
        }

        private static bool Carried(string id)
        {
            return EmporiumEntry.Instance != null && EmporiumEntry.Instance.IsAfterhourHaveOwnedItems(id);
        }

        internal static void ResetBoard()
        {
            cells = null;
            used = null;
            marked = null;
            revealed = null;
            clued = null;
            clueSource = null;
            clueText = null;
            lastClick = -1;
            boardOpened = false;
        }

        internal static bool Open()
        {
            if (CustomUIManager.Instance == null)
            {
                Debug.LogWarning("[ScavArcade] CustomUIManager.Instance is null");
                return false;
            }

            if (window != null && window.IsAlive)
            {
                window.Show();
                return true;
            }

            if (!ScavHelper.CanScavenge())
            {
                return false;
            }

            attemptsLeft = ScavHelper.GetScavTimeLeft();
            if (attemptsLeft <= 0)
            {
                return false;
            }

            try
            {
                hasCrowbar = EmporiumEntry.Instance != null && EmporiumEntry.Instance.IsAfterhourHaveOwnedItems("crowbar");
                hasMagnifier = EmporiumEntry.Instance != null && EmporiumEntry.Instance.IsAfterhourHaveOwnedItems("magnifier");
                hasFlashlight = EmporiumEntry.Instance != null && EmporiumEntry.Instance.IsAfterhourHaveOwnedItems("flashlight");
                if (cells == null)
                {
                    foundCount = 0;
                    ended = false;
                    paused = false;
                    lines.Clear();
                    lastPick.Clear();
                    lightCharges = hasFlashlight ? 3 : 0;
                    inspectCharges = hasMagnifier ? 1 : 0;
                    GenerateBoard();
                }
                if (used == null)
                {
                    used = new bool[CellCount];
                }
                if (marked == null)
                {
                    marked = new bool[CellCount];
                }
                if (revealed == null)
                {
                    revealed = new bool[CellCount];
                }
                if (clued == null)
                {
                    clued = new bool[CellCount];
                }
                if (clueSource == null)
                {
                    clueSource = new int[CellCount];
                }
                if (clueText == null)
                {
                    clueText = new string[CellCount];
                }
                cellElements = new CustomUIElement[CellCount];
                lightMode = false;
                inspectMode = false;

                CustomUIBuilder builder = CustomUIManager
                    .Window(WindowId, TextBank.Get("ui.title"), "overlay")
                    .SetSize(780f, 600f)
                    .SetPosition(new Vector2(90f, 40f))
                    .SetDraggable(true);

                builder.AddLabel("...", "status");
                builder.AddLabel("...", "clue");
                builder.BeginGrid(Columns, 62f, 62f, 4f);
                for (int i = 0; i < CellCount; i++)
                {
                    int index = i;
                    builder.AddButton("?", () => OnCell(index), "cell" + i);
                    cellElements[i] = builder.Last;
                    if (cellElements[i].root != null)
                    {
                        CellFlagClick flag = cellElements[i].root.AddComponent<CellFlagClick>();
                        flag.index = index;
                    }
                }
                builder.End();
                cellBaseColor = new Color[CellCount];
                cellBaseText = new Color[CellCount];
                for (int i = 0; i < CellCount; i++)
                {
                    cellBaseColor[i] = cellElements[i] != null && cellElements[i].image != null ? cellElements[i].image.color : Color.white;
                    cellBaseText[i] = cellElements[i] != null && cellElements[i].text != null ? cellElements[i].text.color : Color.white;
                }
                for (int i = 0; i < CellCount; i++)
                {
                    if (cells != null && cells[i] != null && (used[i] || (revealed != null && revealed[i])))
                    {
                        MarkCell(i, cells[i], used[i]);
                    }
                }
                builder.AddLabel("...", "log");
                if (hasFlashlight)
                {
                    builder.AddButton(TextBank.Get("action.light_count", lightCharges), StartLight, "light");
                }
                if (hasMagnifier)
                {
                    builder.AddButton(TextBank.Get("action.inspect_count", inspectCharges), StartInspect, "inspect");
                }
                builder.OnClose(OnClosed);

                window = builder.Show();
                PlayBeep("ui", true);
                statusLabel = window.Get("status");
                clueLabel = window.Get("clue");
                logLabel = window.Get("log");
                if (logLabel != null)
                {
                    logLabel.SetText(string.Join("\n", lines.ToArray()));
                }
                lightButton = window.Get("light");
                inspectButton = window.Get("inspect");
                UpdateToolButtons();
                if (logLabel != null)
                {
                    logLabel.SetPreferredSize(720f, 110f);
                }
                if (pulseObject == null)
                {
                    pulseObject = new GameObject("ScavArcadePulse");
                    pulseObject.AddComponent<ArcadePulse>();
                }

                if (!boardOpened)
                {
                    boardOpened = true;
                    BuildIntro();
                    AddLine(TextBank.Get("ui.hint_mark"));
                    AddLine(TextBank.Get("ui.legend"));
                }
                if (paused && PlayerStore.Instance != null && !PlayerStore.Instance.healthData.isWoundedFresh)
                {
                    Resume();
                }
                else if (lastClick >= 0)
                {
                    ShowClueForLast();
                }
                else if (clueLabel != null)
                {
                    clueLabel.SetText(TextBank.Get("clue.initial"));
                }
                if (paused)
                {
                    DisableCells();
                }
                UpdateStatus();
                // 不在这里出线索：玩家还没点任何格子。
                Debug.Log("[ScavArcade] window opened, attempts=" + attemptsLeft);
                return true;
            }
            catch (Exception e)
            {
                Debug.LogException(e);
                Close();
                return false;
            }
        }

        internal static void Close()
        {
            CustomUIWindow current = window;
            window = null;
            statusLabel = null;
            clueLabel = null;
            logLabel = null;
            cellElements = null;
            cellBaseColor = null;
            cellBaseText = null;
            lightButton = null;
            inspectButton = null;
            lightMode = false;
            inspectMode = false;
            if (current != null)
            {
                try
                {
                    current.Close();
                }
                catch (Exception e)
                {
                    Debug.LogException(e);
                }
            }
            if (pulseObject != null)
            {
                UnityEngine.Object.Destroy(pulseObject);
                pulseObject = null;
            }
            paused = false;
        }

        private static void OnClosed()
        {
            window = null;
            statusLabel = null;
            clueLabel = null;
            logLabel = null;
            cellElements = null;
            lightButton = null;
            inspectButton = null;
            lightMode = false;
            inspectMode = false;
        }

        private static void GenerateBoard()
        {
            cells = new CellData[CellCount];
            Debug.Log("[ScavArcade] immunity minor=" + PlayerStore.Instance.dumpingGroundMinorWoundImmunitySearchesLeft + " major=" + PlayerStore.Instance.dumpingGroundMajorWoundImmunitySearchesLeft + " chance=" + ScavHelper.GetMinorWoundChance().ToString("F2") + "/" + ScavHelper.GetMajorWoundChance().ToString("F2"));
            HashSet<string> backpacks = new HashSet<string>();
            for (int i = 0; i < CellCount; i++)
            {
                cells[i] = RollCell(backpacks);
                Debug.Log("[ScavArcade] gen " + i + " table=" + (cells[i].baseTable ?? "-") + " kind=" + cells[i].kind + " extra=" + cells[i].extra);
            }
            used = new bool[CellCount];
            marked = new bool[CellCount];
            revealed = new bool[CellCount];
            clued = new bool[CellCount];
            clueSource = new int[CellCount];
            clueText = new string[CellCount];
            cellElements = new CustomUIElement[CellCount];
            lastClick = -1;
            Debug.Log("[ScavArcade] board generated");
        }

        private static CellData RollCell(HashSet<string> backpacks)
        {
            CellData cell = new CellData();
            expectingBaseSpawn = false;
            bool minorImmune = PlayerStore.Instance.dumpingGroundMinorWoundImmunitySearchesLeft > 0;
            bool majorImmune = PlayerStore.Instance.dumpingGroundMajorWoundImmunitySearchesLeft > 0;
            if (!minorImmune && ScavHelper.RollMinorWound())
            {
                if (HealthData.RollLuck())
                {
                    cell.kind = KindEmpty;
                    return cell;
                }
                cell.kind = KindInjured;
                cell.major = false;
                return cell;
            }
            if (!majorImmune && ScavHelper.RollMajorWound())
            {
                if (HealthData.RollLuck())
                {
                    cell.kind = KindEmpty;
                    return cell;
                }
                cell.kind = KindInjured;
                cell.major = true;
                return cell;
            }
            if (HealthData.RollBadLuck())
            {
                cell.kind = KindEmpty;
                return cell;
            }

            GameItem backpack;
            List<GameItem> items;
            rollingCell = cell;
            try
            {
                items = ScavHelper.GetRandomScavengedItem(out backpack);
            }
            finally
            {
                rollingCell = null;
                expectingBaseSpawn = false;
            }
            if (items == null)
            {
                items = new List<GameItem>();
            }
            if (backpack != null && !backpacks.Add(backpack.identifier))
            {
                items.Remove(backpack);
                backpack = null;
            }
            cell.items = items;
            cell.backpack = backpack;
            cell.kind = Classify(items, cell.baseTable, out cell.extra);
            return cell;
        }

        private static int Classify(List<GameItem> items, string baseTable, out bool extra)
        {
            extra = false;
            if (items == null || items.Count == 0)
            {
                return KindEmpty;
            }
            extra = items.Count >= 2;
            bool junk = baseTable == "junkTable" || items[0].IsGameItemType("JUNK");
            if (!junk)
            {
                if (IsMachineItem(items[0]))
                {
                    return KindMachine;
                }
                if (IsSealedItem(items[0]))
                {
                    return KindSealed;
                }
            }
            return KindBase;
        }

        private static bool IsMachineItem(GameItem item)
        {
            if (item == null || !item.IsGameItemType("MODULE"))
            {
                return false;
            }
            try
            {
                int tier = item.GetTagReadonly("MODULE_TIER_INT").GetInt();
                return tier == 1 || tier == 2;
            }
            catch (Exception)
            {
                return false;
            }
        }

        private static bool IsSealedItem(GameItem item)
        {
            if (item == null)
            {
                return false;
            }
            for (int i = 0; i < SealedItemTypes.Length; i++)
            {
                if (item.IsGameItemType(SealedItemTypes[i]))
                {
                    return true;
                }
            }
            return false;
        }

        private static void OnCell(int index)
        {
            if (ended || paused || window == null || used == null || cells == null)
            {
                return;
            }
            if (index < 0 || index >= CellCount || used[index])
            {
                return;
            }

            if (lightMode)
            {
                LightCell(index);
                return;
            }
            if (inspectMode)
            {
                InspectCell(index);
                return;
            }

            CellData cell = cells[index];
            if (cell == null)
            {
                return;
            }
            if (cell.kind == KindSealed && !hasCrowbar)
            {
                AddLine(TextBank.Get("status.no_crowbar"));
                return;
            }

            used[index] = true;
            lastClick = index;
            attemptsLeft--;
            PlayerStore.Instance.scavengingAttempts++;
            RunStats.OnScavengeAttempt();
            MarkCell(index, cell, true);
            PlayBeep("blip");
            Debug.Log("[ScavArcade] cell " + index + " kind=" + cell.kind + " attempts=" + attemptsLeft);

            bool minorImmune = PlayerStore.Instance.dumpingGroundMinorWoundImmunitySearchesLeft > 0;
            bool majorImmune = PlayerStore.Instance.dumpingGroundMajorWoundImmunitySearchesLeft > 0;
            if (minorImmune)
            {
                PlayerStore.Instance.dumpingGroundMinorWoundImmunitySearchesLeft--;
            }
            if (majorImmune)
            {
                PlayerStore.Instance.dumpingGroundMajorWoundImmunitySearchesLeft--;
            }

            if (cell.kind == KindInjured)
            {
                bool immune = cell.major ? majorImmune : minorImmune;
                if (immune)
                {
                    AddLine(TextBank.Get("result.immunity.1"));
                }
                else
                {
                    if (cell.major)
                    {
                        HealthData.ReceiveMajorWound();
                    }
                    else
                    {
                        HealthData.ReceiveMinorWound();
                    }
                    RunStats.OnScavengeInjury(cell.major);
                    AddLine(TextBank.Get(cell.major ? "result.major.1" : "result.minor.1"));
                    Play(cell.major ? "debris_impact" : "debris_impact2");
                    PlayBeep("hurt", true);
                    ShowInjury();
                    if (attemptsLeft <= 0)
                    {
                        End("injured");
                    }
                    else
                    {
                        Pause();
                    }
                    return;
                }
            }
            else if (cell.kind == KindEmpty)
            {
                AddLine(TextBank.Get("result.empty.1"));
            }
            else
            {
                if (cell.kind == KindSealed)
                {
                    AddLine(TextBank.Get("result.pry.1"));
                }
                else if (cell.kind == KindMachine)
                {
                    AddLine(TextBank.Get("result.machine.1"));
                }
                GiveLoot(cell);
            }

            if (ended)
            {
                return;
            }

            UpdateStatus();
            if (attemptsLeft <= 0)
            {
                End("done");
            }
            else
            {
                GenerateClue(index);
            }
        }

        internal static void Tick()
        {
            if (window == null || ended)
            {
                return;
            }
            if (paused && PlayerStore.Instance != null && !PlayerStore.Instance.healthData.isWoundedFresh)
            {
                if (attemptsLeft <= 0)
                {
                    End("injured");
                }
                else
                {
                    Resume();
                }
            }
        }

        private static void Pause()
        {
            paused = true;
            DisableCells();
            AddLine(TextBank.Get("status.wounded_pause"));
            UpdateStatus();
            Debug.Log("[ScavArcade] paused for bandage, attempts=" + attemptsLeft);
        }

        private static void Resume()
        {
            if (!paused || ended)
            {
                return;
            }
            paused = false;
            EnableCells();
            AddLine(TextBank.Get("status.resume"));
            UpdateStatus();
            ShowClueForLast();
            Debug.Log("[ScavArcade] resumed, attempts=" + attemptsLeft);
        }

        private static void DisableCells()
        {
            if (cellElements == null)
            {
                return;
            }
            for (int i = 0; i < cellElements.Length; i++)
            {
                if (cellElements[i] != null)
                {
                    cellElements[i].SetInteractable(false);
                }
            }
        }

        private static void EnableCells()
        {
            if (cellElements == null || used == null)
            {
                return;
            }
            for (int i = 0; i < cellElements.Length; i++)
            {
                if (cellElements[i] != null)
                {
                    cellElements[i].SetInteractable(!used[i]);
                }
            }
        }

        internal static void ToggleMark(int index)
        {
            if (ended || paused || window == null || marked == null || used == null || cellElements == null)
            {
                return;
            }
            if (index < 0 || index >= CellCount || used[index] || cellElements[index] == null)
            {
                return;
            }

            marked[index] = !marked[index];
            if (marked[index])
            {
                cellElements[index].SetText("!");
                cellElements[index].SetTextColor(new Color32(255, 126, 116, 255));
                cellElements[index].SetImageColor(new Color32(124, 38, 38, 255));
            }
            else if (revealed != null && revealed[index] && cells != null && cells[index] != null)
            {
                MarkCell(index, cells[index], false);
            }
            else
            {
                cellElements[index].SetText("?");
                if (cellBaseText != null)
                {
                    cellElements[index].SetTextColor(cellBaseText[index]);
                }
                if (cellBaseColor != null)
                {
                    cellElements[index].SetImageColor(cellBaseColor[index]);
                }
            }
            Debug.Log("[ScavArcade] mark " + index + " = " + marked[index]);
        }

        private static void MarkCell(int index, CellData cell, bool consume)
        {
            if (cell == null || cellElements == null || index < 0 || index >= cellElements.Length || cellElements[index] == null)
            {
                return;
            }
            if (revealed != null)
            {
                revealed[index] = true;
            }

            if (marked != null)
            {
                marked[index] = false;
            }
            if (cellBaseColor != null)
            {
                cellElements[index].SetImageColor(cellBaseColor[index]);
            }

            string mark;
            Color color;
            switch (cell.kind)
            {
                case KindInjured:
                    mark = TextBank.Get("mark.injured");
                    color = new Color32(238, 82, 71, 255);
                    break;
                case KindEmpty:
                    mark = TextBank.Get("mark.empty");
                    color = new Color32(150, 150, 150, 255);
                    break;
                case KindSealed:
                    mark = TextBank.Get("mark.sealed");
                    color = new Color32(223, 184, 108, 255);
                    break;
                case KindMachine:
                    mark = TextBank.Get("mark.machine");
                    color = new Color32(113, 173, 240, 255);
                    break;
                default:
                    mark = TextBank.Get("mark.item");
                    color = new Color32(228, 231, 225, 255);
                    break;
            }
            if (cell.extra && cell.kind != KindInjured && cell.kind != KindEmpty)
            {
                color = new Color32(146, 214, 146, 255);
            }
            cellElements[index].SetText(mark);
            cellElements[index].SetTextColor(color);
            if (consume)
            {
                cellElements[index].SetInteractable(false);
            }
        }

        private static void GiveLoot(CellData cell)
        {
            try
            {
                List<GameItem> items = cell.items;
                if (items == null || items.Count == 0)
                {
                    AddLine(TextBank.Get("result.empty.1"));
                    return;
                }

                RunStats.OnScavengedItems(items);
                GameGridInventory inventory = EmporiumEntry.Instance.afterhourInventory;
                for (int i = 0; i < items.Count; i++)
                {
                    if (items[i] != null)
                    {
                        GraphUtils.TryAcceptAll(inventory, items[i]);
                    }
                }

                GameItem backpack = cell.backpack;
                if (backpack != null)
                {
                    if (backpack.identifier == "satchel")
                    {
                        PlayerStore.Instance.dumpingGroundSatchelFound = true;
                    }
                    else if (backpack.identifier == "kids_backpack")
                    {
                        PlayerStore.Instance.dumpingGroundKidsBackpackFound = true;
                    }
                }

                foundCount += items.Count;
                Debug.Log("[ScavArcade] loot " + items.Count + " found, total=" + foundCount);
                string name = items[0].name;
                if (string.IsNullOrEmpty(name))
                {
                    name = items[0].identifier;
                }
                bool high = items[0].GetBaseValue() >= 70;
                AddLine(Pick(high ? "result.rare" : "result.common", high ? 3 : 4, name));
                if (items.Count > 1)
                {
                    AddLine(TextBank.Get("result.extra.more"));
                }
                if (cell.dismantleTools != null)
                {
                    for (int t = 0; t < cell.dismantleTools.Count; t++)
                    {
                        string tool = cell.dismantleTools[t];
                        string materialId = tool == "screwdriver" ? "nuts_metal" : (tool == "wire_cutter" ? "wire" : "scrap_metal");
                        AddLine(TextBank.Get("result.dismantle." + tool, GetItemName(items, materialId)));
                    }
                }
                if (cell.baseRolls > 1 && EmporiumEntry.Instance != null && EmporiumEntry.Instance.IsAfterhourHaveOwnedItems("metal_scanner"))
                {
                    AddLine(TextBank.Get("status.scan_double"));
                    Debug.Log("[ScavArcade] scanner double, rolls=" + cell.baseRolls + " items=" + items.Count);
                }
                Play("debris");
                if (high || items.Count > 1)
                {
                    PlayBeep("coin");
                }
            }
            catch (Exception e)
            {
                Debug.LogException(e);
                AddLine(TextBank.Get("result.empty.1"));
            }
        }

        private static void Withdraw()
        {
            if (!ended)
            {
                End("withdraw");
            }
        }

        private static void End(string reason)
        {
            if (ended)
            {
                return;
            }
            ended = true;
            paused = false;

            if (cellElements != null)
            {
                for (int i = 0; i < cellElements.Length; i++)
                {
                    if (cellElements[i] != null)
                    {
                        cellElements[i].SetInteractable(false);
                    }
                }
            }

            AddLine(TextBank.Get("end." + reason + ".1"));
            if (foundCount <= 0)
            {
                AddLine(TextBank.Get("end.summary.empty"));
            }
            else
            {
                AddLine(Pick("end.summary", 3, foundCount));
            }
            if (statusLabel != null)
            {
                statusLabel.SetText(TextBank.Get("ui.remaining", 0));
            }
            if (lightButton != null)
            {
                lightButton.SetInteractable(false);
            }
            if (inspectButton != null)
            {
                inspectButton.SetInteractable(false);
            }
            PlayBeep("end", true);
            Debug.Log("[ScavArcade] end " + reason + " found=" + foundCount);
        }

        private static void UpdateStatus()
        {
            if (statusLabel != null)
            {
                string text = TextBank.Get("ui.remaining", Mathf.Max(0, attemptsLeft));
                if (hasFlashlight)
                {
                    text += " · " + TextBank.Get("ui.battery", lightCharges);
                }
                if (hasMagnifier)
                {
                    text += " · " + TextBank.Get("ui.magnifier", inspectCharges);
                }
                if (paused)
                {
                    text += " · " + TextBank.Get("ui.bandage");
                }
                statusLabel.SetText(text);
            }
        }

        private static void EnsureClueArrays()
        {
            if (clueSource == null || clueSource.Length != CellCount)
            {
                clueSource = new int[CellCount];
            }
            if (clueText == null || clueText.Length != CellCount)
            {
                clueText = new string[CellCount];
            }
        }

        private static void ShowClueForLast()
        {
            if (clueLabel == null)
            {
                return;
            }
            if (lastClick < 0)
            {
                clueLabel.SetText(TextBank.Get("clue.initial"));
                return;
            }
            EnsureClueArrays();
            if (lastClick < clueText.Length && !string.IsNullOrEmpty(clueText[lastClick]))
            {
                clueLabel.SetText(clueText[lastClick]);
                return;
            }
            GenerateClue(lastClick);
        }

        private static void StoreClue(int click, int source, string text)
        {
            EnsureClueArrays();
            if (click >= 0 && click < clueText.Length)
            {
                clueSource[click] = source;
                clueText[click] = text;
            }
            if (clueLabel != null)
            {
                clueLabel.SetText(text);
            }
        }

        private static void GenerateClue(int click)
        {
            if (clueLabel == null || used == null || cells == null || click < 0 || click >= CellCount)
            {
                return;
            }
            EnsureClueArrays();
            if (click < clueText.Length && !string.IsNullOrEmpty(clueText[click]))
            {
                // 同一格只抽一次线索；重复调用只回放已存文本。
                clueLabel.SetText(clueText[click]);
                return;
            }
            if (clued == null) clued = new bool[CellCount];
            if (revealed == null) revealed = new bool[CellCount];

            int cx = click % Columns;
            int cy = click / Columns;
            List<int> candidates = new List<int>();
            for (int dy = -1; dy <= 1; dy++)
            {
                for (int dx = -1; dx <= 1; dx++)
                {
                    if (dx == 0 && dy == 0) continue;
                    int x = cx + dx;
                    int y = cy + dy;
                    if (x < 0 || x >= Columns || y < 0 || y >= Rows) continue;
                    int n = y * Columns + x;
                    if (used[n] || cells[n] == null || revealed[n] || clued[n]) continue;
                    candidates.Add(n);
                }
            }

            if (candidates.Count == 0)
            {
                StoreClue(click, -1, TextBank.Get("clue.quiet.1"));
                Debug.Log("[ScavArcade] clue click=" + click + " quiet");
                return;
            }

            int source = -1;
            List<int> hazards = new List<int>();
            for (int i = 0; i < candidates.Count; i++)
            {
                int n = candidates[i];
                if (cells[n].kind == KindInjured) hazards.Add(n);
            }
            if (hazards.Count > 0)
            {
                source = hazards[rng.Next(hazards.Count)];
            }
            else
            {
                int bestValue = -1;
                List<int> best = new List<int>();
                for (int i = 0; i < candidates.Count; i++)
                {
                    int n = candidates[i];
                    int value = CellValue(cells[n]);
                    if (value > bestValue)
                    {
                        bestValue = value;
                        best.Clear();
                        best.Add(n);
                    }
                    else if (value == bestValue)
                    {
                        best.Add(n);
                    }
                }
                source = best[rng.Next(best.Count)];
            }

            CellData sourceCell = cells[source];
            string key;
            int count;
            if (sourceCell.kind == KindInjured)
            {
                key = "clue.hazard";
                count = 4;
            }
            else if (sourceCell.kind == KindMachine)
            {
                key = "clue.machine";
                count = 2;
            }
            else if (sourceCell.kind == KindSealed)
            {
                key = "clue.sealed";
                count = 2;
            }
            else if (sourceCell.kind == KindEmpty)
            {
                key = "clue.empty";
                count = 3;
            }
            else if (CellValue(sourceCell) >= 70)
            {
                key = "clue.rare";
                count = 3;
            }
            else if (sourceCell.extra)
            {
                key = "clue.extra";
                count = 2;
            }
            else
            {
                key = "clue.item";
                count = 3;
            }

            clued[source] = true;
            if (sourceCell.extra && sourceCell.kind != KindInjured && sourceCell.kind != KindEmpty)
            {
                MarkCell(source, sourceCell, false);
            }

            StoreClue(click, source, CompassTo(click, source) + " · " + Pick(key, count));
            Debug.Log("[ScavArcade] clue click=" + click + " " + key + " source=" + source + " value=" + CellValue(sourceCell) + " neighbors=" + candidates.Count);
        }

        private static string CompassTo(int from, int to)
        {
            int dx = (to % Columns) - (from % Columns);
            int dy = (to / Columns) - (from / Columns);
            if (dx == 0 && dy == 0)
            {
                return "";
            }
            if (dx == 0)
            {
                return TextBank.Get(dy < 0 ? "dir.n" : "dir.s");
            }
            if (dy == 0)
            {
                return TextBank.Get(dx > 0 ? "dir.e" : "dir.w");
            }
            if (dx > 0)
            {
                return TextBank.Get(dy < 0 ? "dir.ne" : "dir.se");
            }
            return TextBank.Get(dy < 0 ? "dir.nw" : "dir.sw");
        }

        private static int CellValue(CellData cell)
        {
            if (cell == null || cell.items == null)
            {
                return 0;
            }
            int total = 0;
            for (int i = 0; i < cell.items.Count; i++)
            {
                if (cell.items[i] != null)
                {
                    total += (int)cell.items[i].GetBaseValue();
                }
            }
            return total;
        }

        private static void StartInspect()
        {
            if (ended || paused || window == null)
            {
                return;
            }
            if (inspectCharges <= 0)
            {
                AddLine(TextBank.Get("status.inspect_used"));
                return;
            }
            if (inspectMode)
            {
                inspectMode = false;
                AddLine(TextBank.Get("status.inspect_cancel"));
                return;
            }
            lightMode = false;
            inspectMode = true;
            AddLine(TextBank.Get("status.inspect_prompt"));
            PlayBeep("ui", true);
        }

        private static void StartLight()
        {
            if (ended || paused || window == null)
            {
                return;
            }
            if (lightCharges <= 0)
            {
                AddLine(TextBank.Get("status.light_used"));
                return;
            }
            if (lightMode)
            {
                lightMode = false;
                AddLine(TextBank.Get("status.light_cancel"));
                return;
            }
            inspectMode = false;
            lightMode = true;
            AddLine(TextBank.Get("status.light_prompt"));
            PlayBeep("ui", true);
        }

        private static void InspectCell(int index)
        {
            inspectMode = false;
            if (cells == null || index < 0 || index >= CellCount || cells[index] == null)
            {
                return;
            }
            inspectCharges--;
            CellData cell = cells[index];
            string text;
            if (cell.kind == KindInjured)
            {
                text = TextBank.Get("result.inspect.hazard.1");
            }
            else if (cell.kind == KindEmpty)
            {
                text = TextBank.Get("result.inspect.empty.1");
            }
            else
            {
                string names = GetItemNames(cell.items);
                if (string.IsNullOrEmpty(names))
                {
                    text = TextBank.Get("result.inspect.empty.1");
                }
                else if (cell.kind == KindSealed)
                {
                    text = TextBank.Get("result.inspect.sealed_named", names);
                }
                else if (cell.kind == KindMachine)
                {
                    text = TextBank.Get("result.inspect.machine_named", names);
                }
                else
                {
                    text = TextBank.Get("result.inspect.named", names);
                }
            }
            AddLine(text);
            MarkCell(index, cell, false);
            UpdateToolButtons();
            UpdateStatus();
            Debug.Log("[ScavArcade] inspect " + index + " kind=" + cell.kind + " charges=" + inspectCharges);
        }

        private static void LightCell(int index)
        {
            lightMode = false;
            if (cells == null || index < 0 || index >= CellCount || cells[index] == null)
            {
                return;
            }
            lightCharges--;
            CellData cell = cells[index];
            string text;
            switch (cell.kind)
            {
                case KindInjured:
                    text = TextBank.Get("result.light.hazard.1");
                    break;
                case KindSealed:
                    text = TextBank.Get("result.light.sealed.1");
                    break;
                case KindMachine:
                    text = TextBank.Get("result.light.machine.1");
                    break;
                case KindBase:
                    text = TextBank.Get("result.light.base.1");
                    break;
                default:
                    text = TextBank.Get("result.light.safe.1");
                    break;
            }
            if (cell.extra)
            {
                text = TextBank.Get("result.light.extra.1");
            }
            AddLine(text);
            if (lightCharges == 1)
            {
                AddLine(TextBank.Get("status.low_battery"));
            }
            else if (lightCharges == 0)
            {
                AddLine(TextBank.Get("status.light_used"));
            }
            MarkCell(index, cell, false);
            UpdateToolButtons();
            UpdateStatus();
            Debug.Log("[ScavArcade] light " + index + " kind=" + cell.kind + " battery=" + lightCharges);
        }

        private static string GetItemName(List<GameItem> items, string id)
        {
            if (items != null)
            {
                for (int i = 0; i < items.Count; i++)
                {
                    if (items[i] != null && items[i].identifier == id)
                    {
                        string name = items[i].name;
                        return string.IsNullOrEmpty(name) ? id : name;
                    }
                }
            }
            return id;
        }

        private static string GetItemNames(List<GameItem> items)
        {
            if (items == null || items.Count == 0)
            {
                return null;
            }
            List<string> names = new List<string>();
            for (int i = 0; i < items.Count; i++)
            {
                if (items[i] == null)
                {
                    continue;
                }
                string name = items[i].name;
                if (string.IsNullOrEmpty(name))
                {
                    name = items[i].identifier;
                }
                if (!string.IsNullOrEmpty(name))
                {
                    names.Add(name);
                }
            }
            return names.Count == 0 ? null : string.Join(TextBank.Get("ui.list_sep"), names.ToArray());
        }

        private static void UpdateToolButtons()
        {
            if (lightButton != null)
            {
                if (lightCharges > 0)
                {
                    lightButton.SetInteractable(true);
                    lightButton.SetText(TextBank.Get("action.light_count", lightCharges));
                }
                else
                {
                    lightButton.SetInteractable(false);
                    lightButton.SetText(TextBank.Get("action.light_used"));
                }
            }
            if (inspectButton != null)
            {
                if (inspectCharges > 0)
                {
                    inspectButton.SetInteractable(true);
                    inspectButton.SetText(TextBank.Get("action.inspect_count", inspectCharges));
                }
                else
                {
                    inspectButton.SetInteractable(false);
                    inspectButton.SetText(TextBank.Get("action.inspect_used"));
                }
            }
        }

        private static void BuildIntro()
        {
            AddLine(Pick("intro.base", 6));
            try
            {
                bool fresh = false;
                bool georgio = false;
                AfterhourLocation location = AfterhourLocation.Get("dumping_ground");
                if (location != null && location.ActiveEvents != null)
                {
                    for (int i = 0; i < location.ActiveEvents.Count; i++)
                    {
                        if (location.ActiveEvents[i].id == "fresh_dump")
                        {
                            fresh = true;
                        }
                        else if (location.ActiveEvents[i].id == "georgio_assistance")
                        {
                            georgio = true;
                        }
                    }
                }

                if (fresh)
                {
                    AddLine(Pick("intro.new_trash", 2));
                }
                else if (georgio)
                {
                    AddLine(Pick("intro.george", 2));
                }
                else if (StartingPerk.IsCarefulScavenger())
                {
                    AddLine(Pick("intro.careful", 1));
                }
                else if (StartingPerk.IsDegenerativeOsteoarthritis())
                {
                    AddLine(Pick("intro.osteo", 1));
                }

                List<string> tools = new List<string>();
                AddTool(tools, "flashlight");
                AddTool(tools, "metal_scanner");
                AddTool(tools, "crowbar");
                AddTool(tools, "magnifier");
                AddTool(tools, "welder");
                AddTool(tools, "wire_cutter");
                AddTool(tools, "screwdriver");
                if (tools.Count > 0)
                {
                    AddLine(Pick("intro.tool." + tools[rng.Next(tools.Count)], 1));
                }
            }
            catch (Exception e)
            {
                Debug.LogException(e);
            }
        }

        private static void AddTool(List<string> tools, string id)
        {
            if (EmporiumEntry.Instance != null && EmporiumEntry.Instance.IsAfterhourHaveOwnedItems(id))
            {
                tools.Add(id);
            }
        }

        private static string Pick(string slot, int count, params object[] args)
        {
            int index;
            int last;
            lastPick.TryGetValue(slot, out last);
            do
            {
                index = rng.Next(count) + 1;
            }
            while (count > 1 && index == last);
            lastPick[slot] = index;
            return TextBank.Get(slot + "." + index, args);
        }

        private static void AddLine(string text)
        {
            if (string.IsNullOrEmpty(text))
            {
                return;
            }
            lines.Add(text);
            if (lines.Count > 5)
            {
                lines.RemoveAt(0);
            }
            if (logLabel != null)
            {
                logLabel.SetText(string.Join("\n", lines.ToArray()));
            }
        }

        private static void PlayBeep(string key, bool second = false)
        {
            try
            {
                bool ok = second
                    ? ModHelper.PlaySound2(ScavArcadeMod.ModId, key)
                    : ModHelper.PlaySound(ScavArcadeMod.ModId, key);
                if (!ok)
                {
                    Debug.LogWarning("[ScavArcade] sound missing: " + key);
                }
            }
            catch (Exception e)
            {
                Debug.LogException(e);
            }
        }

        private static void Play(string sound)
        {
            try
            {
                if (AudioManager.Instance != null)
                {
                    AudioManager.Instance.Play2(sound);
                }
            }
            catch (Exception e)
            {
                Debug.LogException(e);
            }
        }

        private static void ShowInjury()
        {
            try
            {
                GameGridInventory grid = EmporiumEntry.Instance != null ? EmporiumEntry.Instance.afterhourInventory : null;
                if (grid == null || grid.inner == null || grid.inner.rectTransform == null)
                {
                    return;
                }

                RectTransform root = grid.inner.rectTransform;
                GameObject go = new GameObject(
                    "Scav arcade injury",
                    typeof(RectTransform),
                    typeof(CanvasRenderer),
                    typeof(Image));
                go.layer = root.gameObject.layer;
                RectTransform rect = go.GetComponent<RectTransform>();
                rect.SetParent(root, false);
                rect.anchorMin = Vector2.zero;
                rect.anchorMax = Vector2.one;
                rect.offsetMin = Vector2.zero;
                rect.offsetMax = Vector2.zero;

                Image background = go.GetComponent<Image>();
                background.color = new Color32(121, 32, 37, 125);
                background.raycastTarget = false;

                MakeBar(rect, new Vector2(96f, 7f));
                MakeBar(rect, new Vector2(7f, 96f));
                go.transform.SetAsLastSibling();
                ArcadeFade fade = go.AddComponent<ArcadeFade>();
                fade.Begin(0.08f, 0.28f);
            }
            catch (Exception e)
            {
                Debug.LogException(e);
            }
        }

        private static void MakeBar(RectTransform parent, Vector2 size)
        {
            GameObject go = new GameObject(
                "Scav arcade cross",
                typeof(RectTransform),
                typeof(CanvasRenderer),
                typeof(Image));
            go.layer = parent.gameObject.layer;
            RectTransform rect = go.GetComponent<RectTransform>();
            rect.SetParent(parent, false);
            rect.anchorMin = new Vector2(0.5f, 0.5f);
            rect.anchorMax = new Vector2(0.5f, 0.5f);
            rect.pivot = new Vector2(0.5f, 0.5f);
            rect.anchoredPosition = Vector2.zero;
            rect.sizeDelta = size;

            Image image = go.GetComponent<Image>();
            image.color = new Color32(245, 235, 215, 255);
            image.raycastTarget = false;
        }
        private static string AutoTestDir()
        {
            try
            {
                return ModHelper.GetModDataFolder(ScavArcadeMod.ModId);
            }
            catch (Exception)
            {
                return null;
            }
        }

        private static void MaybeStartAutoTest()
        {
            try
            {
                string dir = AutoTestDir();
                if (dir == null)
                {
                    return;
                }
                if (!ModHelper.ModDataFileExists(ScavArcadeMod.ModId, "autotest.flag"))
                {
                    return;
                }
                ModHelper.DeleteModDataFile(ScavArcadeMod.ModId, "autotest.flag");
                autoTestReportPath = dir + "\\autotest-report.txt";
                autoTestLines.Clear();
                autoTestPass = 0;
                autoTestFail = 0;
                autoTestActive = true;
                autoTestStep = 0;
                autoTestWait = 0.8f;
                AutoTestLog("start dir=" + dir);
                EnsurePulse();
            }
            catch (Exception e)
            {
                Debug.LogException(e);
            }
        }

        private static void EnsurePulse()
        {
            if (pulseObject == null)
            {
                pulseObject = new GameObject("ScavArcadePulse");
                pulseObject.AddComponent<ArcadePulse>();
            }
        }

        internal static void AutoTestTick()
        {
            if (!autoTestActive)
            {
                return;
            }
            autoTestWait -= Time.deltaTime;
            if (autoTestWait > 0f)
            {
                return;
            }
            try
            {
                switch (autoTestStep)
                {
                    case 0: AutoTestOpen(); break;
                    case 1: AutoTestBoard(); break;
                    case 2: AutoTestSealed(); break;
                    case 3: AutoTestFlashlight(); break;
                    case 4: AutoTestMagnifier(); break;
                    case 5: AutoTestExtra(); break;
                    case 6: AutoTestClick(); break;
                    default: AutoTestFinish(); break;
                }
            }
            catch (Exception e)
            {
                AutoTestFail("exception: " + e);
                AutoTestFinish();
            }
        }

        private static void AutoTestNext(int step, float wait = 0.5f)
        {
            autoTestStep = step;
            autoTestWait = wait;
        }

        private static void AutoTestOpen()
        {
            if (!Open())
            {
                AutoTestFail("Open() returned false (no attempts or no UI)");
                AutoTestFinish();
                return;
            }
            AutoTestPass("Open()");
            AutoTestNext(1, 0.8f);
        }

        private static void AutoTestBoard()
        {
            AutoTestCheck(cells != null && cells.Length == CellCount, "board has 24 cells");
            if (cells == null)
            {
                AutoTestFinish();
                return;
            }
            int injured = 0, empty = 0, baseCount = 0, sealedCount = 0, machine = 0, extra = 0;
            for (int i = 0; i < cells.Length; i++)
            {
                CellData c = cells[i];
                if (c == null)
                {
                    AutoTestFail("cell " + i + " is null");
                    continue;
                }
                switch (c.kind)
                {
                    case KindInjured: injured++; break;
                    case KindEmpty: empty++; break;
                    case KindSealed: sealedCount++; break;
                    case KindMachine: machine++; break;
                    default: baseCount++; break;
                }
                if (c.extra) extra++;
                AutoTestCheck(c.extra == (c.items != null && c.items.Count >= 2), "cell " + i + " extra flag");
            }
            AutoTestLog("board injured=" + injured + " empty=" + empty + " base=" + baseCount + " sealed=" + sealedCount + " machine=" + machine + " extra=" + extra);
            if (PlayerStore.Instance.dumpingGroundMinorWoundImmunitySearchesLeft > 0 || PlayerStore.Instance.dumpingGroundMajorWoundImmunitySearchesLeft > 0)
            {
                AutoTestCheck(injured == 0, "immunity implies no injury cells");
            }
            AutoTestNext(2);
        }

        private static void AutoTestSealed()
        {
            int idx = FindFirstUnusedKind(KindSealed);
            if (idx < 0)
            {
                AutoTestSkip("no unrevealed sealed cell");
            }
            else if (hasCrowbar)
            {
                AutoTestSkip("crowbar owned; no-crowbar case not testable");
            }
            else
            {
                int before = attemptsLeft;
                OnCell(idx);
                AutoTestCheck(attemptsLeft == before, "sealed without crowbar keeps attempts");
                AutoTestCheck(!used[idx], "sealed without crowbar stays unused");
            }
            AutoTestNext(3);
        }

        private static void AutoTestFlashlight()
        {
            if (!hasFlashlight)
            {
                AutoTestSkip("no flashlight");
            }
            else
            {
                int idx = FindFirstUnused();
                if (idx < 0)
                {
                    AutoTestSkip("no unused cell for flashlight");
                }
                else
                {
                    int before = attemptsLeft;
                    int charges = lightCharges;
                    StartLight();
                    LightCell(idx);
                    AutoTestCheck(attemptsLeft == before, "flashlight keeps attempts");
                    AutoTestCheck(lightCharges == charges - 1, "flashlight battery -1");
                }
            }
            AutoTestNext(4);
        }

        private static void AutoTestMagnifier()
        {
            if (!hasMagnifier)
            {
                AutoTestSkip("no magnifier");
            }
            else
            {
                int idx = FindFirstUnused();
                if (idx < 0)
                {
                    AutoTestSkip("no unused cell for magnifier");
                }
                else
                {
                    int before = attemptsLeft;
                    int charges = inspectCharges;
                    StartInspect();
                    InspectCell(idx);
                    AutoTestCheck(attemptsLeft == before, "magnifier keeps attempts");
                    AutoTestCheck(inspectCharges == charges - 1, "magnifier charges -1");
                }
            }
            AutoTestNext(5);
        }

        private static void AutoTestExtra()
        {
            int idx = FindFirstUnusedExtra();
            if (idx < 0)
            {
                AutoTestSkip("no unrevealed extra cell");
            }
            else
            {
                MarkCell(idx, cells[idx], false);
                bool green = cellElements != null && cellElements[idx] != null && cellElements[idx].text != null
                    && cellElements[idx].text.color == (Color)new Color32(146, 214, 146, 255);
                AutoTestCheck(green, "extra cell mark is green");
            }
            AutoTestNext(6);
        }

        private static void AutoTestClick()
        {
            int idx = FindFirstUnusedSafe();
            if (idx < 0)
            {
                AutoTestSkip("no safe unrevealed cell");
                AutoTestFinish();
                return;
            }
            int before = attemptsLeft;
            OnCell(idx);
            AutoTestCheck(attemptsLeft == before - 1, "normal click consumes one attempt");

            int source = clueSource != null ? clueSource[idx] : -1;
            string text = clueText != null ? clueText[idx] : null;
            AutoTestCheck(!string.IsNullOrEmpty(text), "click generates clue for clicked cell");
            int cluedBefore = CountClued();
            if (!string.IsNullOrEmpty(text))
            {
                ShowClueForLast();
                AutoTestCheck(text == clueText[idx], "reopen keeps the clue bound to the clicked cell");
                AutoTestCheck(CountClued() == cluedBefore, "reopen does not consume a new clue source");
            }

            int idx2 = FindFirstUnusedSafe();
            if (idx2 >= 0)
            {
                OnCell(idx2);
                int source2 = clueSource != null ? clueSource[idx2] : -1;
                AutoTestCheck(source2 < 0 || source2 != source, "next click does not reuse the clue source");
            }
            AutoTestNext(7);
        }

        private static int CountClued()
        {
            if (clued == null)
            {
                return 0;
            }
            int count = 0;
            for (int i = 0; i < clued.Length; i++)
            {
                if (clued[i]) count++;
            }
            return count;
        }

        private static void AutoTestFinish()
        {
            if (!autoTestActive)
            {
                return;
            }
            autoTestActive = false;
            string summary = "PASS=" + autoTestPass + " FAIL=" + autoTestFail;
            AutoTestLog(summary);
            try
            {
                if (!string.IsNullOrEmpty(autoTestReportPath))
                {
                    ModHelper.WriteModDataFileText(ScavArcadeMod.ModId, "autotest-report.txt", string.Join("\n", autoTestLines.ToArray()));
                }
            }
            catch (Exception e)
            {
                Debug.LogException(e);
            }
            Debug.Log("[ScavArcade][AutoTest] " + summary);
        }

        private static void AutoTestCheck(bool ok, string what)
        {
            if (ok)
            {
                AutoTestPass(what);
            }
            else
            {
                AutoTestFail(what);
            }
        }

        private static void AutoTestPass(string what)
        {
            autoTestPass++;
            AutoTestLog("PASS " + what);
        }

        private static void AutoTestFail(string what)
        {
            autoTestFail++;
            AutoTestLog("FAIL " + what);
        }

        private static void AutoTestSkip(string what)
        {
            AutoTestLog("SKIP " + what);
        }

        private static void AutoTestLog(string line)
        {
            autoTestLines.Add(line);
            Debug.Log("[ScavArcade][AutoTest] " + line);
        }

        private static int FindFirstUnusedKind(int kind)
        {
            for (int i = 0; i < CellCount; i++)
            {
                if (!used[i] && cells[i] != null && cells[i].kind == kind)
                {
                    return i;
                }
            }
            return -1;
        }

        private static int FindFirstUnused()
        {
            for (int i = 0; i < CellCount; i++)
            {
                if (!used[i] && cells[i] != null)
                {
                    return i;
                }
            }
            return -1;
        }

        private static int FindFirstUnusedExtra()
        {
            for (int i = 0; i < CellCount; i++)
            {
                if (!used[i] && cells[i] != null && cells[i].extra)
                {
                    return i;
                }
            }
            return -1;
        }

        private static int FindFirstUnusedSafe()
        {
            for (int i = 0; i < CellCount; i++)
            {
                if (used[i] || cells[i] == null)
                {
                    continue;
                }
                if (cells[i].kind == KindInjured || cells[i].kind == KindEmpty)
                {
                    continue;
                }
                if (cells[i].kind == KindSealed && !hasCrowbar)
                {
                    continue;
                }
                return i;
            }
            return -1;
        }
    }

    internal sealed class CellFlagClick : MonoBehaviour, IPointerClickHandler
    {
        public int index;

        public void OnPointerClick(PointerEventData eventData)
        {
            if (eventData != null && eventData.button == PointerEventData.InputButton.Right)
            {
                ArcadeWindow.ToggleMark(index);
            }
        }
    }
}
