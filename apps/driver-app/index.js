import { registerRootComponent } from 'expo';
import App from './App';

// Safely extract component function handling ES module default export interop
const RootApp = App && App.default ? App.default : App;

registerRootComponent(RootApp);
