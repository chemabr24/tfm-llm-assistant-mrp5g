using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Networking;
using System.Text;
using TMPro; 
using UnityEngine.UI;
using System.Text.RegularExpressions;

public class APIManager : MonoBehaviour
{
    [Header("Configuración API")]
    public string apiBaseUrl = "http://192.168.1.18:8000/api";
    public string sessionId = "1ba98b01-a7ad-47f6-8903-91916f6627b4";
    
    [Header("Scroll")]
    public ScrollRect scrollRect;
    public RectTransform contentRect;
    [Header("UI")]
    public TMP_Text responseText;

    private List<Dictionary<string, string>> history = new List<Dictionary<string, string>>();
    private StringBuilder conversationLog = new StringBuilder();

    public System.Action OnQueryFinished;

    public void SendQuery(string query)
    {
        StartCoroutine(SendQueryCoroutine(query));
    }

    private IEnumerator SendQueryCoroutine(string query)
    {
        // Añadimos la pregunta del médico al log inmediatamente
        conversationLog.AppendLine($"<b>Tú:</b> {query}");
        conversationLog.AppendLine();
        conversationLog.AppendLine("<i>Procesando consulta...</i>");
        responseText.text = conversationLog.ToString();
        RefreshChatLayout();

        var requestBody = new QueryRequest
        {
            query = query,
            session_id = sessionId,
            history = history
        };

        string jsonBody = JsonUtility.ToJson(requestBody);
        byte[] bodyRaw = Encoding.UTF8.GetBytes(jsonBody);

        using (UnityWebRequest request = new UnityWebRequest(apiBaseUrl + "/chat", "POST"))
        {
            request.uploadHandler = new UploadHandlerRaw(bodyRaw);
            request.downloadHandler = new DownloadHandlerBuffer();
            request.SetRequestHeader("Content-Type", "application/json");

            yield return request.SendWebRequest();
            Debug.Log($"[SendQuery] Result: {request.result} | Código HTTP: {request.responseCode} | Respuesta cruda: '{request.downloadHandler.text}' | Error: {request.error}");
            // Quitamos la línea "Procesando consulta..." que habíamos añadido
            RemoveLastLine();

            if (request.result == UnityWebRequest.Result.Success)
            {
                string response = request.downloadHandler.text;
                if (response.Contains("__SOURCES__"))
                {
                    response = response.Split(new string[] { "__SOURCES__" }, System.StringSplitOptions.None)[0];
                }
                response = response.Trim();
                string displayResponse  = MarkdownToTMP(response);

                if (string.IsNullOrEmpty(response))
                {
                    response = "No se ha podido generar una respuesta. Inténtalo de nuevo.";
                }

                conversationLog.AppendLine($"<b>Asistente:</b> {displayResponse }");
                conversationLog.AppendLine();
                conversationLog.AppendLine("――――――――――――――――");
                conversationLog.AppendLine();

                history.Add(new Dictionary<string, string> { { "role", "user" }, { "content", query } });
                history.Add(new Dictionary<string, string> { { "role", "assistant" }, { "content", response } });
            }
            else
            {
                conversationLog.AppendLine($"<color=red>Error al conectar con el asistente: {request.error}</color>");
                conversationLog.AppendLine();
            }

            responseText.text = conversationLog.ToString();
            RefreshChatLayout();
            OnQueryFinished?.Invoke();
        }
    }

    private void RemoveLastLine()
    {
        string text = conversationLog.ToString();
        int lastLineStart = text.LastIndexOf("<i>Procesando consulta...</i>");
        if (lastLineStart >= 0)
        {
            conversationLog.Length = lastLineStart;
        }
    }

    public void CreateSession(string title, string patientId)
    {
        Debug.Log("CreateSession llamado con título: " + title);
        StartCoroutine(CreateSessionCoroutine(title, patientId));
    }

    private IEnumerator CreateSessionCoroutine(string title, string patientId)
    {
        Debug.Log("Enviando petición a: " + apiBaseUrl + "/sessions");
        var requestBody = new SessionRequest
        {
            title = title,
            patient_identifier = patientId
        };

        string jsonBody = JsonUtility.ToJson(requestBody);
        byte[] bodyRaw = Encoding.UTF8.GetBytes(jsonBody);

        using (UnityWebRequest request = new UnityWebRequest(apiBaseUrl + "/sessions", "POST"))
        {
            request.uploadHandler = new UploadHandlerRaw(bodyRaw);
            request.downloadHandler = new DownloadHandlerBuffer();
            request.SetRequestHeader("Content-Type", "application/json");

            yield return request.SendWebRequest();
            Debug.Log("Resultado: " + request.result);
            Debug.Log("Código HTTP: " + request.responseCode);
            Debug.Log("Respuesta: " + request.downloadHandler.text);
            Debug.Log("Error: " + request.error);

            if (request.result == UnityWebRequest.Result.Success)
            {
                SessionResponse response = JsonUtility.FromJson<SessionResponse>(request.downloadHandler.text);
                sessionId = response.id;
                Debug.Log("Sesión creada: " + sessionId);
            }
        }
    }
    private void RefreshChatLayout()
    {
        StartCoroutine(RefreshChatLayoutCoroutine());
    }

    private IEnumerator RefreshChatLayoutCoroutine()
    {
        // Esperamos al final del frame para asegurar que TMP_Text ya proceso el texto nuevo
        yield return new WaitForEndOfFrame();

        Canvas.ForceUpdateCanvases();
        if (contentRect != null)
            LayoutRebuilder.ForceRebuildLayoutImmediate(contentRect);

        yield return null; // un frame más de margen tras el rebuild

        if (scrollRect != null)
            scrollRect.verticalNormalizedPosition = 0f;

        Debug.Log($"[RefreshChatLayout] Content height: {(contentRect != null ? contentRect.rect.height : -1)}");
    }

    private static string MarkdownToTMP(string text)
    {
        if (string.IsNullOrEmpty(text)) return text;

        // Restos de HTML de documentos antiguos: los cierres de párrafo/lista
        // se convierten en salto de línea (para no pegar frases), y las etiquetas
        // de apertura simplemente se eliminan.
        text = Regex.Replace(text, @"</(p|li)>", "\n");
        text = Regex.Replace(text, @"<(p|ul|li|strong|em|br)\s*/?>", "");

        // Negrita: **texto** -> <b>texto</b>
        text = Regex.Replace(text, @"\*\*(.+?)\*\*", "<b>$1</b>");

        // Cursiva: *texto* o _texto_ -> <i>texto</i>
        text = Regex.Replace(text, @"(?<!\*)\*(?!\*)(.+?)\*(?!\*)", "<i>$1</i>");
        text = Regex.Replace(text, @"_(.+?)_", "<i>$1</i>");

        // Encabezados Markdown (#, ##, ###) -> línea en negrita
        text = Regex.Replace(text, @"^#{1,6}\s*(.+)$", "<b>$1</b>", RegexOptions.Multiline);

        // Tablas Markdown -> líneas "Etiqueta: contenido"
        text = ConvertMarkdownTables(text);

        // Viñetas "- item" o "* item" -> "• item"
        text = Regex.Replace(text, @"^\s*[-*]\s+", "• ", RegexOptions.Multiline);

        return text;
    }

    private static string ConvertMarkdownTables(string text)
    {
        var lines = text.Split('\n');
        var result = new StringBuilder();

        foreach (var rawLine in lines)
        {
            string line = rawLine.Trim();

            if (line.Length == 0)
            {
                result.AppendLine();
                continue;
            }

            // Fila separadora de tabla: |---|---| -> se descarta
            if (Regex.IsMatch(line, @"^\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)+\|?$"))
            {
                continue;
            }

            // Fila de tabla: | Col1 | Col2 | ... |
            if (line.StartsWith("|") && line.EndsWith("|"))
            {
                var cells = line.Trim('|').Split('|');
                for (int i = 0; i < cells.Length; i++)
                {
                    cells[i] = cells[i].Trim();
                }

                if (cells.Length >= 2 && cells[0].Length > 0)
                {
                    // La celda ya puede venir en <b>...</b> si era **texto** en Markdown.
                    // En ese caso solo insertamos los dos puntos antes del cierre,
                    // en vez de volver a envolverla en otra etiqueta <b>.
                    string label = cells[0];
                    if (label.EndsWith("</b>"))
                        label = label.Substring(0, label.Length - 4) + ":</b>";
                    else
                        label = $"<b>{label}:</b>";

                    string content = string.Join(" ", cells, 1, cells.Length - 1).Trim();
                    result.AppendLine($"{label} {content}");
                }
                else if (cells.Length == 1 && cells[0].Length > 0)
                {
                    result.AppendLine(cells[0]);
                }
                continue;
            }

            result.AppendLine(line);
        }

        return result.ToString();
    }
}

[System.Serializable]
public class QueryRequest
{
    public string query;
    public string session_id;
    public List<Dictionary<string, string>> history;
}

[System.Serializable]
public class SessionRequest
{
    public string title;
    public string patient_identifier;
}

[System.Serializable]
public class SessionResponse
{
    public string id;
    public string title;
}