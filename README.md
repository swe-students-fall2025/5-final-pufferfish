# Final Project

[![CI](https://github.com/swe-students-fall2025/5-final-pufferfish/actions/workflows/webapp-ci.yml/badge.svg)](https://github.com/swe-students-fall2025/5-final-pufferfish/actions/workflows/webapp-ci.yml)
[![CD](https://github.com/swe-students-fall2025/5-final-pufferfish/actions/workflows/docker-cicd.yml/badge.svg)](https://github.com/swe-students-fall2025/5-final-pufferfish/actions/workflows/docker-cicd.yml)

An exercise to put to practice software development teamwork, subsystem communication, containers, deployment, and CI/CD pipelines. See [instructions](./instructions.md) for details.

## Introduction

**Pufferfish** is a collaborative resume review and feedback platform designed to help users improve their resumes through peer feedback and interactive review tools. Pufferfish provides a seamless experience for resume submission, viewing, and collaborative feedback.

Users can fill out a form with their personal information, education, work experience, skills, and projects. After completing the form, users can select from a variety of professional resume templates, and Pufferfish will generate a polished PDF resume ready for download. Additionally, users can upload their existing resume and use our templates to create multiple versions of their resume, allowing them to experiment with different formats and styles.

**Note:** Our name "Pufferfish" comes from the fact that we're using Digital Ocean for hosting, and there are fishes in the ocean! 🐡


### Design & Wireframes

We have created comprehensive wireframes and design mockups in Figma to guide the development process. These wireframes illustrate the user interface, user flows, and overall design system for the application. ([See our Figma](https://www.figma.com/design/N6CbB635KE2QMmKGgWY8J9/Pufferfish?node-id=0-1&t=eNVqs4hYh1AwZWWP-1))

## Features

- **User Authentication**: Secure signup and login system with password hashing
- **Resume Form Submission**: Manual resume entry or pdf upload with a comprehensive form including:
  - Personal contact information
  - Education history
  - Work experience with detailed bullet points
  - Skills and project listings
- **Interactive Resume Viewer**: View resumes with interactive features for feedback
- **Resume Feedback System**: Collaborative feedback tools allowing users to highlight and comment on resumes
- **User Profiles**: Personal profile pages to view your resume and feedback received

## Class Members

- Alex Xie ([axie22](https://github.com/axie22))
- Coco Liu ([yiminliu2004](https://github.com/yiminliu2004))
- David Shen ([SnazzyBeatle115](https://github.com/SnazzyBeatle115))
- Phoebe Huang ([phoebelh](https://github.com/phoebelh))
- Xiaomin Liu ([xl4624](https://github.com/xl4624))

## Setup and Installation

Deployment link: https://pufferfish-36n2u.ondigitalocean.app/ 

### Setup

1. Navigate to the project root directory:

   ```bash
   cd /path/to/5-final-pufferfish
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

### Docker Setup

To run the application using Docker Compose:

```bash
docker-compose up
```

The application will be available at `http://localhost:8000`

## Deployment

The CI/CD pipeline should just reference these secrets configured in this GitHub repository's settings:

| Secret | Description |
|--------|-------------|
| `DOCKERHUB_USERNAME` | Docker Hub username |
| `DOCKERHUB_TOKEN` | Docker Hub personal access token |
| `DIGITALOCEAN_ACCESS_TOKEN` | Digital Ocean API token |
