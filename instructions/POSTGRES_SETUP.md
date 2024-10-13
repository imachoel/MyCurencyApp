
### Set Up Local PostgreSQL Database

Follow these steps to set up a PostgreSQL database locally using Docker:

#### 1. Install Docker

Ensure that Docker is installed on your machine. You can download it from the [Docker website](https://www.docker.com/get-started).

#### 2. Pull the PostgreSQL Docker Image

Open your terminal and run the following command to pull the latest PostgreSQL image from Docker Hub:

```bash
docker pull postgres
```

#### 3. Run the PostgreSQL Container

To start a new PostgreSQL container, use the following command. Replace `<your_password>` with a secure password for the PostgreSQL user.

```bash
docker run --name postgres_container \
  --network my_network \
  -e POSTGRES_USER=<your_username> \
  -e POSTGRES_PASSWORD=<your_password> \
  -e POSTGRES_DB=<db_name> \
  -p 5432:5432 \
  -d postgres
```

#### 4. Optional: Persisting Data

To ensure that your PostgreSQL data persists even after the container is removed, you can mount a volume. Modify the `docker run` command as follows:

```bash
docker run --name postgres_container \
  --network my_network \
  -e POSTGRES_USER=<my_user> \
  -e POSTGRES_PASSWORD=<your_password> \
  -e POSTGRES_DB=<my_database> \
  -p 5432:5432 \
  -v pgdata:/var/lib/postgresql/data \
  -d postgres
```

#### 5. Accessing PostgreSQL

You can connect to your PostgreSQL database using a client like `psql` or any GUI tool (e.g., pgAdmin) using the following connection details:

- **Host**: `localhost`
- **Port**: `5432`
- **Username**: `<your_username>`
- **Password**: `<your_password>`
- **Database Name**: `<database_name>`