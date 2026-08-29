## Project Setup

### Backend Setup

1. Clone the repository and navigate to the project root:

```bash
git clone https://github.com/hisuperaman/index-r.git
cd index-r
```

2. Install dependencies and create a virtual environment using Pipenv:

```bash
pipenv install
pipenv shell
```

3. Create a .env file in the root directory with the following template:

```bash
ALLOWED_HOSTS=*
SECRET_KEY=YOUR_SECRET_KEY_HERE
RDS_HOSTNAME=localhost
RDS_DB_NAME=indexr
RDS_USERNAME=
RDS_PASSWORD=
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=YOUR_EMAIL_ADDRESS
EMAIL_HOST_PASSWORD=YOUR_EMAIL_PASSWORD
```

4. Apply migrations:

```bash
python manage.py migrate
```

5. Create a superuser:

```bash
python manage.py createsuperuser
```

6. Start the backend server:

```bash
python manage.py runserver
```

### Frontend Setup

1. Navigate to the frontend directory:

```bash
cd webapp
```

2. Install dependencies:

```bash
yarn install
```

3. Start the frontend server:

```bash
yarn run dev
```

### Adding UI Components

This project uses **shadcn/ui**. Add UI components using the shadcn CLI.

```bash
yarn shadcn add <component>
```

For example, to add the `button` component:

```bash
yarn shadcn add button
```
