const { remote } = require('webdriverio');

// Configura le capabilities
const capabilities = {
    platformName: 'Android',
    'appium:automationName': 'UiAutomator2',
        'appium:deviceName': 'Android',
        'appium:appPackage': 'com.android.settings',
        'appium:appActivity': '.Settings',
      
};

// Opzioni per la connessione Appium
const options = {
    hostname: 'http://127.0.0.1',
    port: 4723,
    path: '/wd/hub',
    capabilities: capabilities
};

async function getUIDump() {
    try {
        // Connetti al server Appium
        console.log('Connessione al server Appium...');
        const driver = await remote(options);

        // Ottieni il dump della pagina
        console.log('Recupero dump UI...');
        const pageSource = await driver.getPageSource();
        
        // Stampa o elabora il dump
        console.log('Dump UI:');
        console.log(pageSource);

        // Chiudi la sessione
        await driver.deleteSession();
        
    } catch (error) {
        console.error('Errore:', error.message);
    }
}

// Esegui il dump
getUIDump();