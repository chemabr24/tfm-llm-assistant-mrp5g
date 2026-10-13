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
                description =
                    "Evaluación inicial de la presión arterial según la guía ESC 2024.",
                isFinal = false,
                options = new List<ProtocolOption>
                {
                    new ProtocolOption
                    {
                        label = "Clasificar presión arterial",
                        nextNodeId = 1
                    },
                    new ProtocolOption
                    {
                        label = "Cifras muy elevadas o síntomas graves",
                        nextNodeId = 2
                    }
                }
            },

            new ProtocolNode
            {
                id = 1,
                title = "Clasificación de la presión arterial",
                description =
                    "Clasifique la presión arterial medida en consulta según las categorías ESC 2024.",
                isFinal = false,
                options = new List<ProtocolOption>
                {
                    new ProtocolOption
                    {
                        label = "PA no elevada (<120/70 mmHg)",
                        nextNodeId = 3
                    },
                    new ProtocolOption
                    {
                        label = "PA elevada (120-139/70-89 mmHg)",
                        nextNodeId = 4
                    },
                    new ProtocolOption
                    {
                        label = "Hipertensión (≥140/90 mmHg)",
                        nextNodeId = 5
                    }
                }
            },

            new ProtocolNode
            {
                id = 2,
                title = "Cifras muy elevadas",
                description =
                    "Ante una presión arterial igual o superior a 180/110 mmHg debe descartarse una emergencia hipertensiva.",
                isFinal = false,
                options = new List<ProtocolOption>
                {
                    new ProtocolOption
                    {
                        label = "Signos o síntomas de emergencia",
                        nextNodeId = 6
                    },
                    new ProtocolOption
                    {
                        label = "Sin signos de emergencia",
                        nextNodeId = 7
                    }
                }
            },

            new ProtocolNode
            {
                id = 3,
                title = "Presión arterial no elevada",
                description =
                    "Presión arterial en consulta inferior a 120 mmHg sistólica y 70 mmHg diastólica.",
                isFinal = false,
                options = new List<ProtocolOption>
                {
                    new ProtocolOption
                    {
                        label = "Paciente menor de 40 años",
                        nextNodeId = 8
                    },
                    new ProtocolOption
                    {
                        label = "Paciente de 40 años o más",
                        nextNodeId = 9
                    }
                }
            },

            new ProtocolNode
            {
                id = 4,
                title = "Presión arterial elevada",
                description =
                    "Presión arterial sistólica de 120-139 mmHg y/o diastólica de 70-89 mmHg. El manejo depende del riesgo cardiovascular.",
                isFinal = false,
                options = new List<ProtocolOption>
                {
                    new ProtocolOption
                    {
                        label = "Valorar riesgo cardiovascular",
                        nextNodeId = 10
                    },
                    new ProtocolOption
                    {
                        label = "Aplicar cambios en estilo de vida",
                        nextNodeId = 11
                    }
                }
            },

            new ProtocolNode
            {
                id = 5,
                title = "Hipertensión",
                description =
                    "Presión arterial en consulta igual o superior a 140/90 mmHg. El diagnóstico debe confirmarse preferentemente mediante AMPA o MAPA.",
                isFinal = false,
                options = new List<ProtocolOption>
                {
                    new ProtocolOption
                    {
                        label = "140-159/90-99 mmHg",
                        nextNodeId = 12
                    },
                    new ProtocolOption
                    {
                        label = "160-179/100-109 mmHg",
                        nextNodeId = 13
                    },
                    new ProtocolOption
                    {
                        label = "≥180/110 mmHg",
                        nextNodeId = 2
                    }
                }
            },

            new ProtocolNode
            {
                id = 6,
                title = "Posible emergencia hipertensiva",
                description =
                    "La presencia de daño agudo de órgano diana o signos clínicos compatibles requiere evaluación y tratamiento inmediato.",
                isFinal = true,
                options = new List<ProtocolOption>()
            },

            new ProtocolNode
            {
                id = 7,
                title = "Hipertensión grave sin emergencia",
                description =
                    "Si la presión arterial es ≥180/110 mmHg pero no existe una emergencia hipertensiva, puede confirmarse lo antes posible, preferentemente antes de una semana.",
                isFinal = true,
                options = new List<ProtocolOption>()
            },

            new ProtocolNode
            {
                id = 8,
                title = "Cribado en menores de 40 años",
                description =
                    "En adultos menores de 40 años con presión arterial no elevada se puede considerar un cribado oportunista al menos cada 3 años.",
                isFinal = true,
                options = new List<ProtocolOption>()
            },

            new ProtocolNode
            {
                id = 9,
                title = "Cribado en adultos de 40 años o más",
                description =
                    "En adultos de 40 años o más se puede considerar un cribado oportunista de la presión arterial al menos una vez al año.",
                isFinal = true,
                options = new List<ProtocolOption>()
            },

            new ProtocolNode
            {
                id = 10,
                title = "Evaluación del riesgo cardiovascular",
                description =
                    "En pacientes con presión arterial elevada debe evaluarse el riesgo cardiovascular. Se consideran de riesgo aumentado, entre otros, pacientes con enfermedad cardiovascular establecida, enfermedad renal crónica moderada o grave, daño orgánico mediado por hipertensión, diabetes o hipercolesterolemia familiar. En otros pacientes se puede utilizar SCORE2 o SCORE2-OP.",
                isFinal = false,
                options = new List<ProtocolOption>
                {
                    new ProtocolOption
                    {
                        label = "Riesgo cardiovascular aumentado",
                        nextNodeId = 14
                    },
                    new ProtocolOption
                    {
                        label = "Riesgo no aumentado",
                        nextNodeId = 15
                    }
                }
            },

            new ProtocolNode
            {
                id = 11,
                title = "Cambios en el estilo de vida",
                description =
                    "En pacientes con presión arterial elevada se recomiendan modificaciones del estilo de vida como primera medida. La guía propone mantener estas intervenciones durante aproximadamente tres meses antes de considerar tratamiento farmacológico en pacientes con riesgo elevado.",
                isFinal = true,
                options = new List<ProtocolOption>()
            },

            new ProtocolNode
            {
                id = 12,
                title = "Confirmación de hipertensión",
                description =
                    "Con cifras de 140-159/90-99 mmHg, el diagnóstico debe confirmarse mediante AMPA o MAPA. Si no fuese posible, puede repetirse la medición estandarizada en más de una visita.",
                isFinal = false,
                options = new List<ProtocolOption>
                {
                    new ProtocolOption
                    {
                        label = "Hipertensión confirmada",
                        nextNodeId = 16
                    },
                    new ProtocolOption
                    {
                        label = "Hipertensión no confirmada",
                        nextNodeId = 17
                    }
                }
            },

            new ProtocolNode
            {
                id = 13,
                title = "Hipertensión de mayor intensidad",
                description =
                    "Con cifras de 160-179/100-109 mmHg, la presión arterial debe confirmarse lo antes posible, preferentemente mediante AMPA o MAPA y antes de un mes.",
                isFinal = false,
                options = new List<ProtocolOption>
                {
                    new ProtocolOption
                    {
                        label = "Hipertensión confirmada",
                        nextNodeId = 16
                    }
                }
            },

            new ProtocolNode
            {
                id = 14,
                title = "PA elevada con riesgo cardiovascular aumentado",
                description =
                    "En pacientes con presión arterial elevada y riesgo cardiovascular aumentado se recomiendan cambios en el estilo de vida y reevaluación posterior. Si la presión arterial se mantiene elevada, puede valorarse tratamiento farmacológico según las recomendaciones de la guía.",
                isFinal = true,
                options = new List<ProtocolOption>()
            },

            new ProtocolNode
            {
                id = 15,
                title = "PA elevada sin riesgo cardiovascular aumentado",
                description =
                    "En pacientes con presión arterial elevada y riesgo cardiovascular no aumentado se recomiendan principalmente cambios en el estilo de vida y seguimiento periódico.",
                isFinal = true,
                options = new List<ProtocolOption>()
            },

            new ProtocolNode
            {
                id = 16,
                title = "Hipertensión confirmada",
                description =
                    "En pacientes con hipertensión confirmada se recomienda combinar cambios en el estilo de vida y tratamiento farmacológico, individualizando el manejo según el riesgo cardiovascular, la tolerancia y las características del paciente.",
                isFinal = false,
                options = new List<ProtocolOption>
                {
                    new ProtocolOption
                    {
                        label = "Seguimiento tras iniciar tratamiento",
                        nextNodeId = 18
                    },
                    new ProtocolOption
                    {
                        label = "Valorar causas secundarias",
                        nextNodeId = 19
                    }
                }
            },

            new ProtocolNode
            {
                id = 17,
                title = "Hipertensión no confirmada",
                description =
                    "Si las mediciones fuera de consulta no confirman hipertensión, debe reevaluarse el patrón de presión arterial y considerar situaciones como el efecto de bata blanca.",
                isFinal = true,
                options = new List<ProtocolOption>()
            },

            new ProtocolNode
            {
                id = 18,
                title = "Seguimiento del tratamiento",
                description =
                    "Tras iniciar el tratamiento antihipertensivo se recomienda realizar controles frecuentes, aproximadamente cada 1-3 meses, hasta alcanzar un adecuado control de la presión arterial.",
                isFinal = true,
                options = new List<ProtocolOption>()
            },

            new ProtocolNode
            {
                id = 19,
                title = "Evaluación de hipertensión secundaria",
                description =
                    "Debe considerarse el estudio de causas secundarias especialmente en pacientes jóvenes, hipertensión resistente o presencia de signos y síntomas sugestivos.",
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

        currentPath.Add(
            new PathStep(
                currentNode.id,
                currentNode.title
            )
        );

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
        if (currentNode == null || apiManager == null)
            return;

        string query =
            "Según la documentación clínica disponible en esta sesión, " +
            "explica cómo debe interpretarse y manejarse el siguiente punto del protocolo: " +
            currentNode.title + ". " +
            currentNode.description +
            " Basa la respuesta únicamente en la documentación disponible y cita las fuentes utilizadas.";

        apiManager.SendQuery(query);
    }

    private void OnOptionClicked(int optionIndex)
    {
        if (
            currentNode == null ||
            optionIndex < 0 ||
            optionIndex >= currentNode.options.Count
        )
        {
            return;
        }

        ProtocolOption selectedOption =
            currentNode.options[optionIndex];

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

    private void OnProgressiveOptionClicked(
        int level,
        int optionIndex)
    {
        if (level < 0 || level >= currentPath.Count)
            return;

        ProtocolNode parentNode =
            nodes.Find(
                n => n.id == currentPath[level].nodeId
            );

        if (parentNode == null)
            return;

        if (
            optionIndex < 0 ||
            optionIndex >= parentNode.options.Count
        )
        {
            return;
        }

        currentNode = parentNode;

        int removeCount =
            currentPath.Count - level - 1;

        if (removeCount > 0)
        {
            currentPath.RemoveRange(
                level + 1,
                removeCount
            );
        }

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
        if (
            pathIndex < 0 ||
            pathIndex >= currentPath.Count
        )
        {
            return;
        }

        PathStep selectedStep =
            currentPath[pathIndex];

        currentNode =
            nodes.Find(
                n => n.id == selectedStep.nodeId
            );

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