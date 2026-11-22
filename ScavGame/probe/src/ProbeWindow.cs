using System;
using UnityEngine;
using UnityEngine.UI;

namespace ScavProbe
{
    internal static class ProbeWindow
    {
        private const string WindowId = "scav_probe_m0";

        private static CustomUIWindow window;

        private static PixelWindow nativeWindow;

        internal static bool Open()
        {
            if (!(CustomUIManager.Instance != null))
            {
                Debug.LogWarning("[ScavProbe] CustomUIManager.Instance is null");
                return false;
            }
            try
            {
                if (CustomUIManager.Instance.IsOpen(WindowId))
                {
                    Refresh("already open");
                    return true;
                }

                CustomUIBuilder builder = CustomUIManager
                    .Window(WindowId, "M0 探针", "overlay")
                    .SetSize(460f, 340f)
                    .SetPosition(new Vector2(200f, 120f))
                    .SetDraggable(true);

                builder.AddLabel("loading...", "status");
                builder.AddButton("生成测试物品 + 最简揭示", SpawnItem);
                builder.AddButton("受伤遮罩（暗红 + 白十字）", ShowInjury);
                builder.AddButton("播放自带音效", PlayBeep);
                builder.AddButton("PixelWindow 开关", TogglePixelWindow);
                builder.AddButton("关闭", Close);
                builder.OnClose(OnClosed);

                window = builder.Show();
                Refresh("window opened");
                return true;
            }
            catch (Exception e)
            {
                Debug.LogException(e);
                return false;
            }
        }

        internal static void Refresh(string message)
        {
            if (window == null)
            {
                return;
            }
            try
            {
                CustomUIElement status = window.Get("status");
                if (status == null)
                {
                    return;
                }
                GameGridInventory grid = EmporiumEntry.Instance != null ? EmporiumEntry.Instance.afterhourInventory : null;
                int elements = 0;
                if (grid != null)
                {
                    try
                    {
                        elements = GraphUtils.FindAllChildrenType<GameItemElement>(grid).Count;
                    }
                    catch
                    {
                        elements = -1;
                    }
                }
                status.SetText(string.Format(
                    "[M0] arrived={0}  grid={1}  items={2}  pixel={3}\n{4}",
                    ProbeMod.Arrived,
                    grid != null,
                    elements,
                    nativeWindow != null ? "open" : "closed",
                    message ?? string.Empty));
            }
            catch (Exception e)
            {
                Debug.LogException(e);
            }
        }

        internal static void Close()
        {
            try
            {
                if (nativeWindow != null)
                {
                    nativeWindow.Destroy();
                    nativeWindow = null;
                }
            }
            catch (Exception e)
            {
                Debug.LogException(e);
            }

            CustomUIWindow current = window;
            window = null;
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
        }

        private static void OnClosed()
        {
            window = null;
        }

        private static void SpawnItem()
        {
            try
            {
                GameGridInventory grid = EmporiumEntry.Instance != null ? EmporiumEntry.Instance.afterhourInventory : null;
                if (grid == null)
                {
                    Refresh("afterhourInventory = null");
                    return;
                }

                GameItem item = ItemSpawner.Spawn("scrap_metal");
                if (item == null)
                {
                    Refresh("ItemSpawner.Spawn returned null");
                    return;
                }

                int added = GraphUtils.TryAcceptAll(grid, item);
                GameItemElement target = null;
                var elements = GraphUtils.FindAllChildrenType<GameItemElement>(grid);
                for (int i = elements.Count - 1; i >= 0; i--)
                {
                    if (elements[i] != null && elements[i].identifier == "scrap_metal")
                    {
                        target = elements[i];
                        break;
                    }
                }

                Refresh(string.Format("spawn added={0} elements={1} target={2}", added, elements.Count, target != null));
                if (target != null)
                {
                    if (target.handler == null)
                    {
                        target.Validate();
                    }
                    Reveal(target);
                }
            }
            catch (Exception e)
            {
                Debug.LogException(e);
                Refresh("spawn exception: " + e.Message);
            }
        }

        private static void Reveal(GameItemElement element)
        {
            try
            {
                if (element == null || element.handler == null || element.handler.rectTransform == null)
                {
                    Refresh("reveal: no handler");
                    return;
                }

                RectTransform root = element.handler.rectTransform;
                GameObject go = new GameObject(
                    "M0 reveal cover",
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

                Image image = go.GetComponent<Image>();
                image.color = new Color(0.05f, 0.06f, 0.07f, 0.95f);
                image.raycastTarget = false;

                M0Fade fade = go.AddComponent<M0Fade>();
                fade.Begin(0.55f, 0.6f);
                Refresh("reveal started");
            }
            catch (Exception e)
            {
                Debug.LogException(e);
                Refresh("reveal exception: " + e.Message);
            }
        }

        private static void ShowInjury()
        {
            try
            {
                GameGridInventory grid = EmporiumEntry.Instance != null ? EmporiumEntry.Instance.afterhourInventory : null;
                if (grid == null || grid.inner == null || grid.inner.rectTransform == null)
                {
                    Refresh("injury: grid/inner is null");
                    return;
                }

                RectTransform root = grid.inner.rectTransform;
                GameObject go = new GameObject(
                    "M0 injury overlay",
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
                M0Fade fade = go.AddComponent<M0Fade>();
                fade.Begin(0.08f, 0.28f);
                Refresh("injury overlay shown");
            }
            catch (Exception e)
            {
                Debug.LogException(e);
                Refresh("injury exception: " + e.Message);
            }
        }

        private static void MakeBar(RectTransform parent, Vector2 size)
        {
            GameObject go = new GameObject(
                "M0 cross",
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

        private static void PlayBeep()
        {
            try
            {
                bool ok = ModHelper.PlaySound(ProbeMod.ModId, "probe_beep");
                Refresh("PlaySound probe_beep = " + ok);
            }
            catch (Exception e)
            {
                Debug.LogException(e);
                Refresh("sound exception: " + e.Message);
            }
        }

        private static void TogglePixelWindow()
        {
            try
            {
                if (nativeWindow != null)
                {
                    nativeWindow.Destroy();
                    nativeWindow = null;
                    Refresh("PixelWindow closed");
                    return;
                }

                GameGridInventory inventory = new GameGridInventory(4, 4);
                inventory.SetMachineryStyle();
                nativeWindow = new PixelWindow(4, 4, true, "M0 PixelWindow", WindowStyle.Classic);
                bool attached = nativeWindow.Attach(inventory);
                nativeWindow.Center();
                nativeWindow.Show();
                Refresh("PixelWindow attached=" + attached);
            }
            catch (Exception e)
            {
                Debug.LogException(e);
                Refresh("PixelWindow exception: " + e.Message);
            }
        }
    }
}
