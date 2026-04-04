# Welcome to your Expo app 👋

This is an [Expo](https://expo.dev) project created with [`create-expo-app`](https://www.npmjs.com/package/create-expo-app).

## Prerequisites: Start the Backend First

Before starting the frontend app, you must start the FastAPI backend:

1. **Get your machine's IP address** — Open PowerShell and run:
   ```bash
   ipconfig
   ```
   Look for your IPv4 Address (e.g., `192.168.x.x` or `10.x.x.x`)

2. **Start the backend** — From the `Backend` folder with virtual environment activated:
   ```bash
   uvicorn main:app --host YOUR_IP_ADDRESS --port 8000
   ```
   Replace `YOUR_IP_ADDRESS` with the IPv4 from ipconfig. For example:
   ```bash
   uvicorn main:app --host 10.123.47.245 --port 8000
   ```

3. **Update frontend config** — Edit `src/config.js` and set:
   ```javascript
   export const API_BASE_URL = 'http://YOUR_IP_ADDRESS:8000';
   ```

4. **Verify backend is running** — Open `http://YOUR_IP_ADDRESS:8000/docs` in your browser to see the API documentation

## Get started

1. Install dependencies

   ```bash
   npm install
   ```

2. Start the app

   ```bash
   npx expo start
   ```

In the output, you'll find options to open the app in a

- [development build](https://docs.expo.dev/develop/development-builds/introduction/)
- [Android emulator](https://docs.expo.dev/workflow/android-studio-emulator/)
- [iOS simulator](https://docs.expo.dev/workflow/ios-simulator/)
- [Expo Go](https://expo.dev/go), a limited sandbox for trying out app development with Expo

You can start developing by editing the files inside the **app** directory. This project uses [file-based routing](https://docs.expo.dev/router/introduction).

## Get a fresh project

When you're ready, run:

```bash
npm run reset-project
```

This command will move the starter code to the **app-example** directory and create a blank **app** directory where you can start developing.

## Learn more

To learn more about developing your project with Expo, look at the following resources:

- [Expo documentation](https://docs.expo.dev/): Learn fundamentals, or go into advanced topics with our [guides](https://docs.expo.dev/guides).
- [Learn Expo tutorial](https://docs.expo.dev/tutorial/introduction/): Follow a step-by-step tutorial where you'll create a project that runs on Android, iOS, and the web.

## Join the community

Join our community of developers creating universal apps.

- [Expo on GitHub](https://github.com/expo/expo): View our open source platform and contribute.
- [Discord community](https://chat.expo.dev): Chat with Expo users and ask questions.
