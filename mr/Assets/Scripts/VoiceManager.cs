using System.Collections;
using UnityEngine;
using TMPro;

public class VoiceManager : MonoBehaviour
{
    [Header("Componentes")]
    public APIManager apiManager;
    public TMP_Text statusText;

    private AudioClip recordingClip;
    private bool isRecording = false;
    private string micDevice;
    private const int SAMPLE_RATE = 16000;
    private const int MAX_RECORDING_SECONDS = 30;

    void Start()
    {
        if (Microphone.devices.Length > 0)
        {
            micDevice = Microphone.devices[0];
            Debug.Log("Micrófono: " + micDevice);
        }
        else
        {
            Debug.LogError("No se encontró ningún micrófono.");
        }
    }

    public void StartListening()
    {
        if (isRecording) return;

        isRecording = true;
        statusText.text = "Escuchando...";
        recordingClip = Microphone.Start(micDevice, false, MAX_RECORDING_SECONDS, SAMPLE_RATE);
        Debug.Log("Grabando audio...");
    }

    public void StopListening()
    {
        if (!isRecording) return;

        isRecording = false;
        Microphone.End(micDevice);
        statusText.text = "Procesando...";
        StartCoroutine(SendAudioToBackend());
    }

    private IEnumerator SendAudioToBackend()
    {
        // Convertir AudioClip a WAV
        byte[] wavData = WavUtility.FromAudioClip(recordingClip);

        WWWForm form = new WWWForm();
        form.AddBinaryData("file", wavData, "audio.wav", "audio/wav");

        using (UnityEngine.Networking.UnityWebRequest request = 
            UnityEngine.Networking.UnityWebRequest.Post(
                apiManager.apiBaseUrl + "/transcribe", form))
        {
            yield return request.SendWebRequest();

            if (request.result == UnityEngine.Networking.UnityWebRequest.Result.Success)
            {
                TranscriptionResponse response = JsonUtility.FromJson<TranscriptionResponse>(
                    request.downloadHandler.text);
                
                if (!string.IsNullOrEmpty(response.text))
                {
                    statusText.text = "Pregunta: " + response.text;
                    apiManager.SendQuery(response.text);
                }
                else
                {
                    statusText.text = "No se detectó voz. Inténtalo de nuevo.";
                }
            }
            else
            {
                statusText.text = "Error al transcribir: " + request.error;
                Debug.LogError("Error transcripción: " + request.error);
            }
        }
    }
}

[System.Serializable]
public class TranscriptionResponse
{
    public string text;
}