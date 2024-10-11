# Smart Click Maps Backend

This backend server handles real-time click data from viewers of the Smart Click Maps Twitch extension. It processes click coordinates, clusters them, and emits the processed data to connected frontend clients for visualization.

## Features

- Real-time WebSocket communication using Flask-SocketIO.
- Click data processing and clustering using the `chatclicks` package.
- JWT authentication to ensure secure communication.
- Integration with Twitch's public keys for token validation.

## Setup Instructions

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/yourusername/smart-click-maps.git
   cd smart-click-maps/backend
