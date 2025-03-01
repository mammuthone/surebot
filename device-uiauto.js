const { remote } = require('webdriverio');
const { exec } = require('child_process');
const util = require('util');
const execPromise = util.promisify(exec);
const path = require('path');

// Configurazione del test
const capabilities = {
  platformName: 'Android',
  'appium:automationName': 'UiAutomator2',
  'appium:deviceName': 'Android',
  'appium:appPackage': 'com.android.settings',
  'appium:appActivity': '.Settings',
};

const wdOpts = {
  hostname: process.env.APPIUM_HOST || 'localhost',
  port: parseInt(process.env.APPIUM_PORT, 10) || 4723,
  logLevel: 'info',
  capabilities,
};

// Funzione per verificare le variabili d'ambiente
async function checkEnvironment() {
    const requiredVars = {
        ANDROID_HOME: process.env.ANDROID_HOME,
        ANDROID_SDK_ROOT: process.env.ANDROID_SDK_ROOT,
    };

    console.log('\nVerifica variabili d\'ambiente:');
    let allValid = true;

    // Verifica presenza variabili
    for (const [name, value] of Object.entries(requiredVars)) {
        if (!value) {
            console.error(`❌ ${name} non impostata`);
            allValid = false;
        } else {
            console.log(`✓ ${name}=${value}`);
        }
    }

    // Verifica esistenza directory
    if (process.env.ANDROID_HOME) {
        try {
            const platformTools = path.join(process.env.ANDROID_HOME, 'platform-tools', 'adb');
            await execPromise(`ls ${platformTools}`);
            console.log('✓ platform-tools trovato');
        } catch (error) {
            console.error('❌ platform-tools non trovato');
            allValid = false;
        }
    }

    // Verifica ADB
    try {
        const { stdout } = await execPromise('adb devices');
        console.log('\nDispositivi connessi:');
        console.log(stdout);
    } catch (error) {
        console.error('❌ ADB non accessibile');
        allValid = false;
    }

    return allValid;
}

// Funzione principale che esegue il test
async function runTest() {
    console.log('Verifico l\'ambiente...');
    const envOk = await checkEnvironment();

    if (!envOk) {
        console.error('\n❌ Configurazione ambiente non valida. Correggere gli errori prima di procedere.');
        console.log('\nSuggerimenti:');
        console.log('1. Aggiungi al tuo ~/.zshrc o ~/.bash_profile:');
        console.log('   export ANDROID_HOME="/Users/username/Library/Android/sdk"');
        console.log('   export ANDROID_SDK_ROOT="/Users/username/Library/Android/sdk"');
        console.log('   export PATH="$ANDROID_HOME/platform-tools:$PATH"');
        console.log('\n2. Ricarica il file di configurazione:');
        console.log('   source ~/.zshrc');
        process.exit(1);
    }

    console.log('\nAvvio test...');
    const driver = await remote(wdOpts);
    try {
        const textItem = await driver.$('//*[@text="Login"]');
        await textItem.click();
        console.log('✓ Test completato con successo');
    } catch (error) {
        console.error('❌ Errore durante il test:', error.message);
        throw error;
    } finally {
        await driver.pause(1000);
        await driver.deleteSession();
    }
}

// Esegui il test
runTest().catch(console.error);