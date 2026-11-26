using UnityEngine;

namespace ScavArcade
{
    internal sealed class ArcadeFade : MonoBehaviour
    {
        private CanvasGroup group;

        private float hold;

        private float fade;

        private float started;

        private bool begun;

        internal void Begin(float holdSeconds, float fadeSeconds)
        {
            group = GetComponent<CanvasGroup>();
            if (group == null)
            {
                group = gameObject.AddComponent<CanvasGroup>();
            }
            group.blocksRaycasts = false;
            group.interactable = false;
            hold = Mathf.Max(0f, holdSeconds);
            fade = Mathf.Max(0.01f, fadeSeconds);
            started = Time.unscaledTime;
            begun = true;
        }

        private void Update()
        {
            if (!begun)
            {
                return;
            }

            float t = Time.unscaledTime - started;
            float alpha = t < hold ? 1f : Mathf.Clamp01(1f - (t - hold) / fade);
            if (group != null)
            {
                group.alpha = alpha;
            }

            if (alpha <= 0f)
            {
                Destroy(gameObject);
            }
        }
    }
}
