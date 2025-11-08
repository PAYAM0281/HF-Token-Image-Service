// WebSocket client for streaming image generation progress

let ws = null;

function getHFToken() {
    // Retrieve HF token from localStorage (managed by HuggingFaceTokenState)
    return localStorage.getItem('hf_token') || '';
}

function startGeneration(params) {
    const token = params.token || getHFToken();
    
    if (!token) {
        console.error('No Hugging Face token available');
        window.dispatchEvent(new CustomEvent('on_generation_error', {
            detail: { message: 'Authentication required. Please set your Hugging Face token.' }
        }));
        return;
    }

    // Close existing connection if any
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.close();
    }

    // Establish WebSocket connection with token authentication
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${wsProtocol}//${window.location.host}/api/v1/stream/generate/txt2img?token=${encodeURIComponent(token)}`;
    
    ws = new WebSocket(wsUrl);

    ws.onopen = function() {
        console.log('WebSocket connected');
        
        // Send generation request
        const request = {
            prompt: params.prompt,
            negative_prompt: params.negative_prompt,
            model_id: params.model_id,
            num_inference_steps: params.num_inference_steps,
            guidance_scale: params.guidance_scale,
            seed: params.seed,
            height: params.height,
            width: params.width,
            lora_path: params.lora_path || null,
            lora_scale: params.lora_scale || 0.8
        };
        
        ws.send(JSON.stringify(request));
        
        // Dispatch generation start event
        window.dispatchEvent(new CustomEvent('on_generation_start', { detail: {} }));
    };

    ws.onmessage = function(event) {
        const data = JSON.parse(event.data);
        
        if (data.type === 'progress') {
            // Dispatch progress update event
            window.dispatchEvent(new CustomEvent('on_generation_progress', {
                detail: { progress: data.progress, step: data.step }
            }));
        } else if (data.type === 'result') {
            // Dispatch completion event with image data
            window.dispatchEvent(new CustomEvent('on_generation_result', {
                detail: { data: data.data }
            }));
            ws.close();
        } else if (data.type === 'error') {
            // Dispatch error event
            window.dispatchEvent(new CustomEvent('on_generation_error', {
                detail: { message: data.message }
            }));
            ws.close();
        }
    };

    ws.onerror = function(error) {
        console.error('WebSocket error:', error);
        window.dispatchEvent(new CustomEvent('on_generation_error', {
            detail: { message: 'WebSocket connection failed' }
        }));
    };

    ws.onclose = function(event) {
        console.log('WebSocket closed:', event.code, event.reason);
    };
}

// Make function available globally
window.startGeneration = startGeneration;
