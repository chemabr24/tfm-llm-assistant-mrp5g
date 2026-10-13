using System;
using System.Collections.Generic;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

public class ProtocolTreeVisualizer : MonoBehaviour
{
    [Header("References")]
    [SerializeField] private RectTransform content;
    [SerializeField] private RectTransform generatedTree;
    [SerializeField] private GameObject nodePrefab;
    [SerializeField] private ScrollRect scrollRect;

    [Header("Layout")]
    [SerializeField] private float nodeWidth = 300f;
    [SerializeField] private float nodeHeight = 90f;
    [SerializeField] private float horizontalSpacing = 80f;
    [SerializeField] private float verticalSpacing = 60f;
    [SerializeField] private float margin = 40f;
    [SerializeField] private float lineThickness = 4f;

    [Header("Node Colors")]
    [SerializeField] private Color optionNodeColor =
        new Color32(216, 234, 247, 255);

    [SerializeField] private Color pathNodeColor =
        new Color32(46, 124, 183, 255);

    [SerializeField] private Color currentNodeColor =
        new Color32(46, 124, 183, 255);

    [SerializeField] private Color lightTextColor =
        new Color32(255, 255, 255, 255);

    [SerializeField] private Color darkTextColor =
        new Color32(18, 49, 74, 255);

    [SerializeField] private Color lineColor =
        new Color32(139, 199, 232, 230);

    public void Render(
        IReadOnlyList<string> path,
        IReadOnlyList<string> options,
        Action<int> onPathNodeClicked = null,
        Action<int> onOptionClicked = null)
    {
        ClearGeneratedTree();

        if (path == null || path.Count == 0)
            return;

        PrepareContent(path.Count, options?.Count ?? 0);

        float rowStep = nodeHeight + verticalSpacing;
        float topY = -margin;

        Vector2 previousPosition = Vector2.zero;

        // -------------------------
        // CAMINO RECORRIDO
        // -------------------------

        for (int i = 0; i < path.Count; i++)
        {
            Vector2 position = new Vector2(
                0f,
                topY - (i * rowStep)
            );

            if (i > 0)
            {
                Vector2 previousNodeBottom  = previousPosition +
                                       new Vector2(0f, -nodeHeight);

                Vector2 childTop = position;

                CreateLine(previousNodeBottom , childTop);
            }

            int pathIndex = i;

            CreateNode(
                path[i],
                position,
                i < path.Count - 1,
                () => onPathNodeClicked?.Invoke(pathIndex)
            );

            previousPosition = position;
        }

        // -------------------------
        // OPCIONES DEL NODO ACTUAL
        // -------------------------

        if (options == null || options.Count == 0)
            return;

        float childrenY = topY - (path.Count * rowStep);

        float totalChildrenWidth =
            (options.Count * nodeWidth) +
            ((options.Count - 1) * horizontalSpacing);

        float firstChildX =
            -(totalChildrenWidth / 2f) +
            (nodeWidth / 2f);

        Vector2 currentNodePosition =
            new Vector2(
                0f,
                topY - ((path.Count - 1) * rowStep)
            );

        Vector2 parentBottom =
            currentNodePosition +
            new Vector2(0f, -nodeHeight);

        for (int i = 0; i < options.Count; i++)
        {
            float x =
                firstChildX +
                (i * (nodeWidth + horizontalSpacing));

            Vector2 childPosition =
                new Vector2(x, childrenY);

            CreateLine(
                parentBottom,
                childPosition
            );

            int optionIndex = i;

            CreateNode(
                options[i],
                childPosition,
                true,
                () => onOptionClicked?.Invoke(optionIndex)
            );
        }

        Canvas.ForceUpdateCanvases();

        // Comenzamos viendo la parte superior del árbol.
        if (scrollRect != null)
        {
            scrollRect.verticalNormalizedPosition = 1f;
        }
    }

    public void RenderProgressive(
        string rootLabel,
        List<bool> pathCanExpand,
        List<List<string>> optionLevels,
        List<List<bool>> optionCanExpand,
        List<int> selectedIndexes,
        Action<int> onPathNodeClicked,
        Action<int, int> onOptionClicked)
    {
        Vector2 previousScrollPosition = content.anchoredPosition;

        if (scrollRect != null)
        {
            scrollRect.StopMovement();
        }

        ClearGeneratedTree();

        if (string.IsNullOrEmpty(rootLabel))
            return;

        float rowStep = nodeHeight + verticalSpacing;
        float topY = -margin;

        // Nodo raíz
        Vector2 parentPosition = new Vector2(0f, topY);

        bool rootIsCurrent = optionLevels.Count == 1;
        bool rootCanExpand =
            pathCanExpand != null &&
            pathCanExpand.Count > 0 &&
            pathCanExpand[0];
        CreateNode(
            rootLabel,
            parentPosition,
            true,
            true,           // pertenece al camino
            rootIsCurrent,  // es el nodo actual si todavía estamos en la raíz
            rootCanExpand,    // nodo expandible
            () => onPathNodeClicked?.Invoke(0)
        );

        float maxAbsX = nodeWidth / 2f;
        int renderedRows = 1;

        for (int level = 0; level < optionLevels.Count; level++)
        {
            List<string> options = optionLevels[level];

            if (options == null || options.Count == 0)
                break;

            int selectedIndex =
                level < selectedIndexes.Count
                    ? selectedIndexes[level]
                    : -1;

            float childrenY =
                topY - ((level + 1) * rowStep);

            float totalWidth =
                (options.Count * nodeWidth) +
                ((options.Count - 1) * horizontalSpacing);

            float firstX =
                parentPosition.x -
                (totalWidth / 2f) +
                (nodeWidth / 2f);

            Vector2 selectedChildPosition = Vector2.zero;
            bool hasSelectedChild = false;

            Vector2 parentBottom =
                parentPosition +
                new Vector2(0f, -nodeHeight);

            for (int i = 0; i < options.Count; i++)
            {
                float x =
                    firstX +
                    (i * (nodeWidth + horizontalSpacing));

                Vector2 childPosition =
                    new Vector2(x, childrenY);

                CreateLine(
                    parentBottom,
                    childPosition
                );

                int capturedLevel = level;
                int capturedOption = i;

                bool canExpand =
                    optionCanExpand != null &&
                    level < optionCanExpand.Count &&
                    optionCanExpand[level] != null &&
                    i < optionCanExpand[level].Count &&
                    optionCanExpand[level][i];

                if (i == selectedIndex)
                {
                    int pathIndex = level + 1;

                    bool isCurrentNode =
                        level == optionLevels.Count - 2;

                    CreateNode(
                        options[i],
                        childPosition,
                        true,
                        true,           // está en el camino seleccionado
                        isCurrentNode,  // último nodo del camino = nodo actual
                        canExpand,  // es un nodo expandible
                        () => onPathNodeClicked?.Invoke(pathIndex)
                    );

                    selectedChildPosition = childPosition;
                    hasSelectedChild = true;
                }
                else
                {
                    CreateNode(
                        options[i],
                        childPosition,
                        true,
                        false,  // no pertenece todavía al camino
                        false,  // no es el nodo actual
                        canExpand,  // es un nodo expandible
                        () => onOptionClicked?.Invoke(
                            capturedLevel,
                            capturedOption
                        )
                    );
                }

                float absX =
                    Mathf.Abs(x) + (nodeWidth / 2f);

                maxAbsX =
                    Mathf.Max(maxAbsX, absX);
            }

            renderedRows = level + 2;

            // Solo seguimos expandiendo por la rama seleccionada.
            if (!hasSelectedChild)
                break;

            parentPosition = selectedChildPosition;
        }

        PrepareProgressiveContent(
            maxAbsX,
            renderedRows
        );

        Canvas.ForceUpdateCanvases();

        content.anchoredPosition = previousScrollPosition;
    }

    private void PrepareProgressiveContent(
        float maxAbsX,
        int rowCount)
    {
        if (content == null)
            return;

        float requiredWidth =
            (maxAbsX * 2f) +
            (margin * 2f);

        float requiredHeight =
            (rowCount * nodeHeight) +
            ((rowCount - 1) * verticalSpacing) +
            (margin * 2f);

        if (scrollRect != null &&
            scrollRect.viewport != null)
        {
            requiredWidth = Mathf.Max(
                requiredWidth,
                scrollRect.viewport.rect.width
            );

            requiredHeight = Mathf.Max(
                requiredHeight,
                scrollRect.viewport.rect.height
            );
        }

        content.anchorMin =
            new Vector2(0.5f, 1f);

        content.anchorMax =
            new Vector2(0.5f, 1f);

        content.pivot =
            new Vector2(0.5f, 1f);

        content.SetSizeWithCurrentAnchors(
            RectTransform.Axis.Horizontal,
            requiredWidth
        );

        content.SetSizeWithCurrentAnchors(
            RectTransform.Axis.Vertical,
            requiredHeight
        );
    }

    private void CreateNode(
    string text,
    Vector2 position,
    bool interactable,
    Action onClick)
    {
        // Compatibilidad con las llamadas actuales.
        // De momento se considera una opción normal.
        CreateNode(
            text,
            position,
            interactable,
            false,
            false,
            false,
            onClick
        );
    }

    private void CreateNode(
        string text,
        Vector2 position,
        bool interactable,
        bool isPathNode,
        bool isCurrentNode,
        bool canExpand,
        Action onClick)
    {
        GameObject node =
            Instantiate(nodePrefab, generatedTree);

        RectTransform rect =
            node.GetComponent<RectTransform>();

        rect.anchorMin = new Vector2(0.5f, 1f);
        rect.anchorMax = new Vector2(0.5f, 1f);
        rect.pivot = new Vector2(0.5f, 1f);

        rect.sizeDelta =
            new Vector2(nodeWidth, nodeHeight);

        rect.anchoredPosition = position;
        rect.localScale = Vector3.one;
        rect.localRotation = Quaternion.identity;

        Image image =
            node.GetComponent<Image>();

        TMP_Text tmp =
            node.GetComponentInChildren<TMP_Text>(true);

        Button button =
            node.GetComponent<Button>();

        Color backgroundColor;
        Color textColor;

        // Prioridad:
        //  Actual > Camino > Opción normal
        if (isCurrentNode)
        {
            backgroundColor = currentNodeColor;
            textColor = lightTextColor;
        }
        else if (isPathNode)
        {
            backgroundColor = pathNodeColor;
            textColor = lightTextColor;
        }
        else
        {
            backgroundColor = optionNodeColor;
            textColor = darkTextColor;
        }

        if (canExpand)
        {
            text += "\n<size=70%>▼</size>";
        }

        if (image != null)
        {
            image.color = backgroundColor;
        }

        if (tmp != null)
        {
            tmp.text = text;
            tmp.color = textColor;
        }

        if (button != null)
        {
            button.onClick.RemoveAllListeners();
            button.interactable = interactable;

            if (interactable && onClick != null)
            {
                button.onClick.AddListener(
                    () => onClick()
                );
            }
        }
    }

    private void CreateLine(
        Vector2 start,
        Vector2 end)
    {
        GameObject lineObject =
            new GameObject(
                "TreeLine",
                typeof(RectTransform),
                typeof(Image)
            );

        lineObject.transform.SetParent(
            generatedTree,
            false
        );

        RectTransform rect =
            lineObject.GetComponent<RectTransform>();

        rect.anchorMin = new Vector2(0.5f, 1f);
        rect.anchorMax = new Vector2(0.5f, 1f);
        rect.pivot = new Vector2(0.5f, 0.5f);

        Vector2 direction = end - start;
        Vector2 middle = (start + end) / 2f;

        rect.anchoredPosition = middle;
        rect.sizeDelta =
            new Vector2(
                direction.magnitude,
                lineThickness
            );

        float angle =
            Mathf.Atan2(
                direction.y,
                direction.x
            ) * Mathf.Rad2Deg;

        rect.localEulerAngles =
            new Vector3(0f, 0f, angle);

        Image image =
            lineObject.GetComponent<Image>();

        image.color = lineColor;
        image.raycastTarget = false;

        // Las líneas siempre por detrás de los nodos.
        lineObject.transform.SetAsFirstSibling();
    }

    private void PrepareContent(
        int pathCount,
        int optionCount)
    {
        if (content == null)
            return;

        RectTransform viewport =
            scrollRect != null
                ? scrollRect.viewport
                : null;

        float viewportWidth =
            viewport != null
                ? viewport.rect.width
                : 0f;

        float viewportHeight =
            viewport != null
                ? viewport.rect.height
                : 0f;

        float requiredWidth = nodeWidth;

        if (optionCount > 0)
        {
            requiredWidth =
                (optionCount * nodeWidth) +
                ((optionCount - 1) * horizontalSpacing);
        }

        requiredWidth += margin * 2f;

        int rows =
            pathCount +
            (optionCount > 0 ? 1 : 0);

        float requiredHeight =
            (rows * nodeHeight) +
            ((rows - 1) * verticalSpacing) +
            (margin * 2f);

        requiredWidth =
            Mathf.Max(
                requiredWidth,
                viewportWidth
            );

        requiredHeight =
            Mathf.Max(
                requiredHeight,
                viewportHeight
            );

        content.anchorMin =
            new Vector2(0.5f, 1f);

        content.anchorMax =
            new Vector2(0.5f, 1f);

        content.pivot =
            new Vector2(0.5f, 1f);

        content.anchoredPosition =
            Vector2.zero;

        content.SetSizeWithCurrentAnchors(
            RectTransform.Axis.Horizontal,
            requiredWidth
        );

        content.SetSizeWithCurrentAnchors(
            RectTransform.Axis.Vertical,
            requiredHeight
        );
    }

    private void ClearGeneratedTree()
    {
        for (
            int i = generatedTree.childCount - 1;
            i >= 0;
            i--
        )
        {
            Destroy(
                generatedTree.GetChild(i).gameObject
            );
        }
    }
}