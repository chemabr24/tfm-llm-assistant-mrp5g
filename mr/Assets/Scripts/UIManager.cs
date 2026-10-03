using UnityEngine;
using TMPro;

public class UIManager : MonoBehaviour
{
    [Header("Paneles")]
    public GameObject responsePanel;
    public GameObject protocolPanel;

    [Header("Textos")]
    public TMP_Text responseText;
    public TMP_Text statusText;
    public TMP_Text sessionInfoText;
    public TMP_Text voiceButtonText;

    [Header("Componentes")]
    public APIManager apiManager;
    public VoiceManager voiceManager;

    private bool isListening = false;

    

    void Start()
    {
        sessionInfoText.text = "Sesión 'Revision HTA'";
        statusText.text = "Pulsa el botón para hablar";
        UpdateVoiceButtonLabel("Hablar");
        apiManager.OnQueryFinished += () => statusText.text = "";
    }

    public void OnVoiceButtonPressed()
    {
        if (!isListening)
        {
            isListening = true;
            voiceManager.StartListening();
            UpdateVoiceButtonLabel("Detener");
        }
        else
        {
            isListening = false;
            voiceManager.StopListening();
            UpdateVoiceButtonLabel("Hablar");
        }
    }

    public void ShowResponsePanel()
    {
        responsePanel.SetActive(true);
        protocolPanel.SetActive(false);
    }

    public void ShowProtocolPanel()
    {
        responsePanel.SetActive(false);
        protocolPanel.SetActive(true);
    }

    void Update()
    {
        // Botón A exclusivamente del controlador derecho:
        // activar/desactivar grabación de voz.
        // Se especifica RTouch para evitar que el gesto de pinch
        // del seguimiento de manos sea interpretado como Button.One.
        if (OVRInput.GetDown(
            OVRInput.Button.One,
            OVRInput.Controller.RTouch
        ))
        {
            OnVoiceButtonPressed();
        }
    }

    private void UpdateVoiceButtonLabel(string label)
    {
        if (voiceButtonText != null)
            voiceButtonText.text = label;
    }
}