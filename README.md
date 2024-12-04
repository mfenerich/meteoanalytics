# Meteo API

Meteo API is a FastAPI-based application designed to provide meteorological data for Antarctica. This project enables retrieval and processing of temperature, pressure, and wind speed data, offering features like time-based aggregation and timezone adjustments.

## **Important Disclaimers**

🚨 **This project is specifically designed to be deployed on macOS systems with an ARM64 architecture.**  

While the code and configuration may work on other platforms, the setup, tooling, and dependencies (such as Docker images and Kubernetes configurations) have been optimized and tested exclusively on **macOS ARM64**. If you are using a different operating system or architecture, additional modifications may be required to ensure compatibility.

### Code Organization

The project is structured into four branches: `main`, `part_1`, `part_2`, and `part_3`. Each branch corresponds to a specific part of the challenge, with `main` being equivalent to `part_3`. This organization allows for easy navigation and clear progression through the challenge phases.

---

## Features

- Fetch real-time or historical weather data for specific stations in Antarctica.
- Aggregate data by hourly, daily, or monthly intervals.
- Adjust timestamps to desired timezones or offsets.
- Cache results using SQLite for faster subsequent queries.
- Routine to clean up old cached data, ensuring efficient use of resources.
- A UI for querying results directly.
- Comprehensive error handling and logging.

## Getting Started

### Prerequisites

- Python 3.11+
- Docker
- Kubernetes (using Kind)

### Running the Project

1. **Build and Start**: 
   Run the following command to create a Kind cluster, deploy all resources, and start the application:
   ```bash
   make build
   ```

2. **Access the Documentation**:
   Once deployed, access the API documentation at:
   [http://localhost:30080/](http://localhost:30080/)

3. **Access the UI**:
   To use the UI for querying results:
   - Run the following command to forward the port:
     ```bash
     kubectl port-forward deployment/meteoservice 30081:8001
     ```
   - Open your browser and navigate to:
     [http://localhost:30081/](http://localhost:30081/)

4. **Teardown**:
   To remove the Kind cluster and all resources:
   ```bash
   make delete_kind_cluster
   ```

## API Endpoints

### Health Check

- **GET** `/health`
  - Check the health of the service.

### Weather Data

- **GET** `/v1/antartida/timeseries/`
  - Retrieve selected weather data for a specified station and time range.
  - Results are cached in SQLite for improved performance.

- **GET** `/v1/antartida/timeseries/full`
  - Retrieve complete weather data for a specified station and time range.
  - Cached data is used if available.

### Cache Management

The application includes a routine to delete old cached data to optimize storage usage. You can customize the retention period through environment variables.

## Development

### Running Tests

Tests are located in the `tests/` directory. Use the following command to run them:

```bash
pytest
```

## Logging and Monitoring

To facilitate system monitoring and debugging, this project generates an **`app.log`** file where all system logs are stored. This log file includes details about API activity, system errors, and general performance metrics.

### Key Features of `app.log`:
- Provides a comprehensive history of system operations.
- Useful for troubleshooting errors and monitoring API performance.
- Designed to support future monitoring integrations like ELK (Elasticsearch, Logstash, Kibana) or Grafana.

The log file is stored in the root directory of the application and is automatically updated during runtime.

## Deployment Architecture

The project uses **Kind** (Kubernetes in Docker) for local testing and deployment, with Kubernetes managing both the API and simulation services.

---

## Prerequisites

### Required Tools and Dependencies
1. **Docker**: Used for containerizing and running the services.
   - Installation: [Docker Documentation](https://docs.docker.com/get-docker/)
2. **Homebrew**: A package manager for macOS, used to install other tools like `kubectl`.
3. **Kubectl**: Command-line tool to interact with Kubernetes.
   - Installation via Homebrew:
     ```bash
     brew install kubectl
     ```
   - **Note**: The `Makefile` automatically installs `kubectl` if not already installed.
4. **GNU Make**: Used to simplify and automate deployment tasks.
   - Installation via Homebrew:
     ```bash
     brew install make
     ```

### Clone the Repository
```bash
git clone https://github.com/mfenerich/meteoanalytics.git
cd meteoanalytics
```

### Build and Deploy Locally
```bash
make build
```
This performs the following tasks:
- Builds and pushes the Docker image.
- Creates the Kind cluster and local registry configuration.
- Deploys all Kubernetes resources.
- 
### Notes on Deployment
- A local Docker registry is used to push and pull images locally.


## Verifying Deployment

### Monitor Pods
```bash
kubectl get po
```

The system will be ready to use when you see something like this:
```bash
NAME                            READY   STATUS    RESTARTS   AGE
meteoservice-666ff74b76-nhw4f   2/2     Running   0          28m
```
---

## CI/CD Pipelines

This project includes a robust CI/CD pipeline implemented using **GitHub Actions**. The pipeline ensures code quality and testing are maintained at every push, improving reliability and streamlining the development process.

### Pipeline Overview

The pipeline is defined in `.github/workflows/pipeline.yml` and consists of two main jobs:

1. **Code Quality Check**:
   - **Purpose**: Ensures that the code adheres to style guidelines and passes pre-commit hooks.
   - **Steps**:
     - Checks out the repository code.
     - Sets up a Python environment using a custom GitHub Action (`setup-environment`).
     - Installs dependencies using Poetry.
     - Runs `ruff` (a fast Python linter) through pre-commit hooks to validate code quality.
   - **Dependencies**:
     - Pre-commit hooks are configured to run automatically during this step.

2. **Run Tests**:
   - **Purpose**: Executes all unit tests to validate the codebase.
   - **Steps**:
     - Waits for the `code-quality` job to complete.
     - Checks out the repository code.
     - Sets up a Python environment using the same custom GitHub Action.
     - Installs dependencies using Poetry.
     - Runs the test suite with `pytest`.
   - **Environment Variables**:
     - Critical configuration values like `DATABASE_URL`, `POSTGRES_USER`, and `POSTGRES_PASSWORD` are passed via environment variables for test execution. Secrets should ideally be stored securely using GitHub's environment variables and secrets management.

### Custom GitHub Action: `setup-environment`

A custom composite action (`action.yaml`) is used to standardize the Python environment setup. This action simplifies the pipeline by handling the installation of specific Python and Poetry versions and caching dependencies for faster builds.

#### `action.yaml`
- **Inputs**:
  - `python-version`: Specifies the Python version to be used (default: 3.11).
  - `poetry-version`: Specifies the Poetry version to be used (default: 1.8.3).
- **Steps**:
  - Installs the specified Poetry version using `pipx`.
  - Sets up the specified Python version using the `actions/setup-python` action, with Poetry package caching enabled.

### Trigger

The pipeline is triggered on every `push` event to the repository.

---

## License

This project is licensed under the [MIT License](https://opensource.org/licenses/MIT).

---

For support or inquiries, please contact:

- **Name:** Marcel
- **Email:** marcel@feneri.ch
- **Website:** [feneri.ch](http://feneri.ch)