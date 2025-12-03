# Final Project

An exercise to put to practice software development teamwork, subsystem communication, containers, deployment, and CI/CD pipelines. See [instructions](./instructions.md) for details.

## Class Members

- Alex Xie ([axie22](https://github.com/axie22))
- Coco Liu ([yiminliu2004](https://github.com/yiminliu2004))
- David Shen ([SnazzyBeatle115](https://github.com/SnazzyBeatle115))
- Phoebe Huang ([phoebelh](https://github.com/phoebelh))
- Xiaomin Liu ([xl4624](https://github.com/xl4624))

## Setup and Installation

Deployment link: https://pufferfish-36n2u.ondigitalocean.app/ 

### Back-End Setup

1. Navigate to the back-end directory:

   ```bash
   cd back-end
   ```

2. Create a virtual environment:

   ```bash
   python3 -m venv venv
   ```

3. Activate the virtual environment:

   ```bash
   source venv/bin/activate
   ```

4. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

5. Run the Flask application:

   ```bash
   python app.py
   ```

   The application will be available at `http://localhost:8000`

### Front-End Setup

1. Navigate to the front-end directory:

   ```bash
   cd front-end
   ```

2. Install dependencies:

   ```bash
   npm install
   ```

3. Run the development server:

   ```bash
   npm run dev
   ```

   The application will be available at `http://localhost:5173`

## Deployment

The CI/CD pipeline should just reference these secrets configured in this GitHub repository's settings:

| Secret | Description |
|--------|-------------|
| `DOCKERHUB_USERNAME` | Docker Hub username |
| `DOCKERHUB_TOKEN` | Docker Hub personal access token |
| `DIGITALOCEAN_ACCESS_TOKEN` | Digital Ocean API token |
