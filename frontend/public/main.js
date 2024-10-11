// frontend/public/main.js

// Initialize Twitch Extension Helper
window.Twitch = window.Twitch || {};
window.Twitch.ext = window.Twitch.ext || {};

let token = '';

window.Twitch.ext.onAuthorized((auth) => {
    token = auth.token;
    const backendURL = 'https://your-backend-server.com'; // Replace with your backend server URL
    const socket = io(backendURL, {
        transports: ['websocket'],
        secure: true,
        rejectUnauthorized: false // Set to true in production with valid SSL
    });

    // Canvas setup
    const canvas = document.getElementById('clickMapCanvas');
    const heatmapInstance = h337.create({
        container: canvas,
        radius: 50,
        maxOpacity: 0.6,
        minOpacity: 0,
        blur: 0.75,
        gradient: {
            '0.0': 'blue',
            '0.5': 'green',
            '1.0': 'red'
        }
    });

    // Resize canvas to fit the stream dimensions
    function resizeCanvas() {
        const width = window.innerWidth;
        const height = window.innerHeight;
        canvas.width = width;
        canvas.height = height;
        heatmapInstance._renderer.setDimensions(width, height);
    }

    window.addEventListener('resize', resizeCanvas);
    resizeCanvas();

    // Capture clicks and send to backend
    canvas.addEventListener('click', (event) => {
        const rect = canvas.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;

        // Normalize coordinates based on original dimensions
        const x_norm = x / canvas.width;
        const y_norm = y / canvas.height;

        // Send click data to backend with token
        socket.emit('user_click', {
            x: x_norm, // Normalized to 0-1
            y: y_norm,
            action: 'leftClick', // or 'rightClick'
            token: token
        });
    });

    // Listen for click data from the backend and update heatmap
    socket.on('click_data', (data) => {
        if (data.type !== 'drag') {
            const point = {
                x: data.x * canvas.width / 1920,  // Adjust for canvas size
                y: data.y * canvas.height / 1080,
                value: 1
            };
            heatmapInstance.addData(point);
        } else {
            // Optionally handle drag actions differently
            // For simplicity, we'll skip drag visualization
        }
    });

    // Listen for errors
    socket.on('error', (data) => {
        console.error(data.message);
    });

    // Listen for acknowledgments
    socket.on('ack', (data) => {
        console.log(data.message);
    });
});

// Handle authentication failure
window.Twitch.ext.onError((error) => {
    console.error('Authentication Error:', error);
});