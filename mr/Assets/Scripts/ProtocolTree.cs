using System.Collections.Generic;
using UnityEngine;
using TMPro;

[System.Serializable]
public class ProtocolOption
{
    public string label;
    public int nextNodeId;
}

[System.Serializable]
public class ProtocolNode
{
    public int id;
    public string title;
    public string description;
    public List<ProtocolOption> options;
    public bool isFinal;
}

public class ProtocolTree : MonoBehaviour
{
    [Header("UI")]
    public TMP_Text titleText;
    public TMP_Text descriptionText;
    public APIManager apiManager;
    [Header("Tree Visualizer")]
    public ProtocolTreeVisualizer treeVisualizer;

    private List<ProtocolNode> nodes;
    private ProtocolNode currentNode;

    private class PathStep
    {
        public int nodeId;
        public string label;

        public PathStep(int nodeId, string label)
        {
            this.nodeId = nodeId;
            this.label = label;
        }
    }

    private List<PathStep> currentPath = new List<PathStep>();

    void Start()
    {
        BuildProtocol();
        ResetProtocol();
    }

    void BuildProtocol()
    {
        nodes = new List<ProtocolNode>
        {
            new ProtocolNode
            {
                id = 0,
                title = "Evaluación inicial",
                description = "El paciente acude a consulta. Seleccione el motivo de la visita.",
                isFinal = false,
                options = new List<ProtocolOption>
                {
                    new ProtocolOption { label = "Medir presión arterial", nextNodeId = 1 },
                    new ProtocolOption { label = "Síntomas graves", nextNodeId = 2 }
                }
            },
            new ProtocolNode
            {
                id = 1,
                title = "Clasificación de la PA",
                description = "Tome dos mediciones en reposo. Seleccione el resultado.",
                isFinal = false,
                options = new List<ProtocolOption>
                {
                    new ProtocolOption { label = "Normal (<130/85 mmHg)", nextNodeId = 3 },
                    new ProtocolOption { label = "Normal-alta (130-139/85-89)", nextNodeId = 4 },
                    new ProtocolOption { label = "HTA (≥140/90 mmHg)", nextNodeId = 5 }
                }
            },
            new ProtocolNode
            {
                id = 2,
                title = "Síntomas graves",
                description = "Paciente con síntomas de emergencia hipertensiva. Derivar a urgencias inmediatamente.",
                isFinal = true,
                options = new List<ProtocolOption>()
            },
            new ProtocolNode
            {
                id = 3,
                title = "Presión arterial normal",
                description = "PA dentro de rangos normales. Recomendar revisión en 12 meses y mantener hábitos saludables.",
                isFinal = true,
                options = new List<ProtocolOption>()
            },
            new ProtocolNode
            {
                id = 4,
                title = "Presión arterial normal-alta",
                description = "PA en rango normal-alto. Recomendar cambios en el estilo de vida y revisión en 6 meses.",
                isFinal = false,
                options = new List<ProtocolOption>
                {
                    new ProtocolOption { label = "Cambios de estilo de vida", nextNodeId = 6 },
                    new ProtocolOption { label = "Factores de riesgo adicionales", nextNodeId = 7 }
                }
            },
            new ProtocolNode
            {
                id = 5,
                title = "Hipertensión arterial",
                description = "PA elevada confirmada. Evaluar el grado de hipertensión.",
                isFinal = false,
                options = new List<ProtocolOption>
                {
                    new ProtocolOption { label = "Grado I (140-159/90-99)", nextNodeId = 8 },
                    new ProtocolOption { label = "Grado II-III (≥160/100)", nextNodeId = 9 }
                }
            },
            new ProtocolNode
            {
                id = 6,
                title = "Cambios de estilo de vida",
                description = "Recomendar dieta baja en sal, ejercicio moderado, reducción del alcohol y control del peso. Revisión en 3 meses.",
                isFinal = true,
                options = new List<ProtocolOption>()
            },
            new ProtocolNode
            {
                id = 7,
                title = "Factores de riesgo adicionales",
                description = "Evaluar factores de riesgo cardiovascular. Considerar inicio de tratamiento farmacológico.",
                isFinal = true,
                options = new List<ProtocolOption>()
            },
            new ProtocolNode
            {
                id = 8,
                title = "HTA Grado I",
                description = "Iniciar tratamiento farmacológico con un fármaco de primera línea. Revisión en 1 mes.",
                isFinal = true,
                options = new List<ProtocolOption>()
            },
            new ProtocolNode
            {
                id = 9,
                title = "HTA Grado II-III",
                description = "Iniciar tratamiento farmacológico combinado urgente. Considerar derivación a cardiología.",
                isFinal = true,
                options = new List<ProtocolOption>()
            }
        };
    }

    private void ResetProtocol()
    {
        currentPath.Clear();

        currentNode = nodes.Find(n => n.id == 0);

        if (currentNode == null)
            return;

        currentPath.Add(new PathStep(
            currentNode.id,
            currentNode.title
        ));

        RefreshTreeUI();
    }

    private void RefreshTreeUI()
    {
        if (currentNode == null)
            return;

        titleText.text = currentNode.title;
        descriptionText.text = currentNode.description;

        if (treeVisualizer == null)
            return;

        List<List<string>> optionLevels =
            new List<List<string>>();

        List<bool> pathCanExpand =
            new List<bool>();

        List<List<bool>> optionCanExpand =
            new List<List<bool>>();

        List<int> selectedIndexes =
            new List<int>();

        for (int level = 0; level < currentPath.Count; level++)
        {
            ProtocolNode node =
                nodes.Find(n => n.id == currentPath[level].nodeId);

            if (node == null)
                continue;

            // Indica si el nodo se puede expandir..
            pathCanExpand.Add(
                node.options != null &&
                node.options.Count > 0
            );

            List<string> labels =
                new List<string>();

            List<bool> expandables =
                new List<bool>();

            foreach (ProtocolOption option in node.options)
            {
                labels.Add(option.label);

                ProtocolNode nextNode =
                    nodes.Find(n => n.id == option.nextNodeId);

                expandables.Add(
                    nextNode != null &&
                    nextNode.options != null &&
                    nextNode.options.Count > 0
                );
            }

            optionLevels.Add(labels);
            optionCanExpand.Add(expandables);

            if (level < currentPath.Count - 1)
            {
                int nextNodeId =
                    currentPath[level + 1].nodeId;

                int selectedIndex =
                    node.options.FindIndex(
                        option =>
                            option.nextNodeId == nextNodeId
                    );

                selectedIndexes.Add(selectedIndex);
            }
            else
            {
                selectedIndexes.Add(-1);
            }
        }

        treeVisualizer.RenderProgressive(
            currentPath[0].label,
            pathCanExpand,
            optionLevels,
            optionCanExpand,
            selectedIndexes,
            OnPathNodeClicked,
            OnProgressiveOptionClicked
        );
    }

    public void AskAssistant()
    {
        if (currentNode == null || apiManager == null) return;
        string query = "Estoy evaluando: " + currentNode.title + ". " + currentNode.description + " ¿Qué me recomiendas?";
        apiManager.SendQuery(query);
    }

    void Update()
    {
        // Botón B del mando derecho:
        // seleccionar la primera opción disponible
        if (
            OVRInput.GetDown(OVRInput.Button.Two) &&
            currentNode != null &&
            currentNode.options.Count > 0
        )
        {
            OnOptionClicked(0);
        }

        // Botón X del mando izquierdo:
        // reiniciar el protocolo
        if (OVRInput.GetDown(OVRInput.Button.Three))
        {
            ResetProtocol();
        }
    }

    private void OnOptionClicked(int optionIndex)
    {
        if (currentNode == null)
            return;

        if (optionIndex < 0 || optionIndex >= currentNode.options.Count)
            return;

        ProtocolOption selectedOption = currentNode.options[optionIndex];

        ProtocolNode nextNode =
            nodes.Find(n => n.id == selectedOption.nextNodeId);

        if (nextNode == null)
            return;

        currentNode = nextNode;

        currentPath.Add(new PathStep(
            nextNode.id,
            selectedOption.label
        ));

        RefreshTreeUI();
    }

    private void OnProgressiveOptionClicked(
        int level,
        int optionIndex)
    {
        if (level < 0 || level >= currentPath.Count)
            return;

        ProtocolNode parentNode =
            nodes.Find(n => n.id == currentPath[level].nodeId);

        if (parentNode == null)
            return;

        if (
            optionIndex < 0 ||
            optionIndex >= parentNode.options.Count
        )
            return;

        // Volvemos conceptualmente a ese nivel.
        currentNode = parentNode;

        // Quitamos todo lo que había por debajo.
        int removeCount =
            currentPath.Count - level - 1;

        if (removeCount > 0)
        {
            currentPath.RemoveRange(
                level + 1,
                removeCount
            );
        }

        // Elegimos la nueva rama.
        ProtocolOption selectedOption =
            parentNode.options[optionIndex];

        ProtocolNode nextNode =
            nodes.Find(
                n => n.id == selectedOption.nextNodeId
            );

        if (nextNode == null)
            return;

        currentNode = nextNode;

        currentPath.Add(
            new PathStep(
                nextNode.id,
                selectedOption.label
            )
        );

        RefreshTreeUI();
    }

    private void OnPathNodeClicked(int pathIndex)
    {
        if (pathIndex < 0 || pathIndex >= currentPath.Count)
            return;

        PathStep selectedStep = currentPath[pathIndex];

        currentNode =
            nodes.Find(n => n.id == selectedStep.nodeId);

        if (currentNode == null)
            return;

        int removeCount =
            currentPath.Count - pathIndex - 1;

        if (removeCount > 0)
        {
            currentPath.RemoveRange(
                pathIndex + 1,
                removeCount
            );
        }

        RefreshTreeUI();
    }
}