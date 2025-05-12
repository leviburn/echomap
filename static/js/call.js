// Call functionality
let callTimer;
let callStartTime;
let currentTranscript = '';
let currentDTMFSequence = [];

function formatPhoneNumber(phoneNumber) {
    // Remove all non-digit characters
    const cleaned = phoneNumber.replace(/\D/g, '');
    
    // If the number starts with 1, remove it
    const withoutCountryCode = cleaned.startsWith('1') ? cleaned.slice(1) : cleaned;
    
    // Add +1 prefix if it's a US number
    return `+1${withoutCountryCode}`;
}

function initCallFunctionality() {
    const makeCallBtn = document.getElementById('makeCallBtn');
    if (makeCallBtn) {
        makeCallBtn.addEventListener('click', handleMakeCall);
    }
}

async function handleMakeCall() {
    const phoneInput = document.getElementById('phone_number');
    const phoneNumber = phoneInput.value.trim();
    
    if (!phoneNumber) {
        showCallStatusModal('Please enter a phone number');
        return;
    }

    // Format the phone number
    const formattedNumber = formatPhoneNumber(phoneNumber);
    
    // Validate the formatted number
    if (formattedNumber.length !== 12) { // +1 + 10 digits
        showCallStatusModal('Please enter a valid US phone number');
        return;
    }

    try {
        showCallStatusModal('Initiating call...');
        
        const response = await fetch('/make-call', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `to_number=${encodeURIComponent(formattedNumber)}`
        });

        const data = await response.json();
        
        if (response.ok) {
            // Show call status
            document.getElementById('callStatus').classList.remove('hidden');
            startCallTimer();
            
            // Show modal with call details
            showCallStatusModal('Call initiated successfully. Waiting for connection...');
            
            // Poll for call status and updates
            pollCallStatus(data.call_sid);
        } else {
            showCallStatusModal(`Error: ${data.error || 'Failed to initiate call'}`);
        }
    } catch (error) {
        console.error('Call error:', error);
        showCallStatusModal(`Error: ${error.message || 'Failed to initiate call'}`);
    }
}

function startCallTimer() {
    callStartTime = Date.now();
    callTimer = setInterval(updateCallTimer, 1000);
}

function updateCallTimer() {
    const elapsed = Math.floor((Date.now() - callStartTime) / 1000);
    const minutes = Math.floor(elapsed / 60).toString().padStart(2, '0');
    const seconds = (elapsed % 60).toString().padStart(2, '0');
    document.getElementById('callTimer').textContent = `${minutes}:${seconds}`;
}

function stopCallTimer() {
    clearInterval(callTimer);
}

async function pollCallStatus(callSid) {
    let attempts = 0;
    const maxAttempts = 60; // 5 minutes maximum (5s * 60)
    
    const checkStatus = async () => {
        if (attempts >= maxAttempts) {
            showCallStatusModal('Call timed out. Please try again.');
            stopCallTimer();
            return;
        }
        
        try {
            console.log(`Polling call status for ${callSid}, attempt ${attempts + 1}`);
            
            // Check for call status updates
            const statusResponse = await fetch(`/call-status?call_sid=${callSid}`);
            if (statusResponse.ok) {
                const statusData = await statusResponse.json();
                console.log('Status data:', statusData);
                
                // Update call status
                let statusMessage = '';
                switch (statusData.status) {
                    case 'initiated':
                        statusMessage = 'Call initiated. Waiting for connection...';
                        break;
                    case 'ringing':
                        statusMessage = 'Call is ringing...';
                        break;
                    case 'in-progress':
                    case 'answered':
                        statusMessage = 'Call connected. Recording in progress...';
                        break;
                    case 'completed':
                        statusMessage = 'Call completed. Processing analysis...';
                        break;
                    default:
                        statusMessage = `Call status: ${statusData.status}`;
                }
                
                // Update DTMF if detected
                if (statusData.dtmf) {
                    console.log('DTMF detected:', statusData.dtmf);
                    currentDTMFSequence.push(statusData.dtmf);
                    showCallStatusModal(statusMessage, statusData.dtmf);
                }
                
                // Update transcript if available
                if (statusData.transcript) {
                    console.log('Transcript updated:', statusData.transcript);
                    currentTranscript = statusData.transcript;
                    showCallStatusModal(statusMessage, null, currentTranscript);
                } else if (statusData.transcription_status === 'in-progress') {
                    showCallStatusModal(statusMessage + ' (Transcribing...)');
                } else {
                    showCallStatusModal(statusMessage);
                }
                
                // Check for analysis completion
                if (statusData.analysis && statusData.analysis.transcript) {
                    console.log('Analysis complete:', statusData.analysis);
                    stopCallTimer();
                    showCallStatusModal('Analysis complete!', null, statusData.analysis.transcript);
                    // Redirect to insights page with the analysis data
                    const params = new URLSearchParams({
                        transcript: statusData.analysis.transcript,
                        flowchart: statusData.analysis.flowchart
                    });
                    window.location.href = `/insights?${params.toString()}`;
                    return;
                }
            } else {
                console.error('Failed to get call status:', await statusResponse.text());
            }
            
            // Continue polling
            attempts++;
            setTimeout(checkStatus, 1000); // Poll more frequently for real-time updates
        } catch (error) {
            console.error('Error polling call status:', error);
            attempts++;
            setTimeout(checkStatus, 5000);
        }
    };
    
    checkStatus();
}

function showCallStatusModal(message, dtmf = null, transcript = null) {
    console.log('Showing status modal:', { message, dtmf, transcript });
    const modal = document.getElementById('callStatusModal');
    const content = document.getElementById('modalContent');
    content.textContent = message;
    modal.style.display = 'block';
    
    if (dtmf) {
        updateDTMFSequence(dtmf);
    }
    
    if (transcript) {
        updateLiveTranscript(transcript);
    }
}

function closeCallStatusModal() {
    const modal = document.getElementById('callStatusModal');
    modal.style.display = 'none';
}

// Initialize call functionality when the page loads
document.addEventListener('DOMContentLoaded', initCallFunctionality); 