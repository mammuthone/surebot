const { exec } = require('child_process');
const util = require('util');
const execPromise = util.promisify(exec);

const ADB_PATH = '/Users/igor/Library/Android/sdk/platform-tools/adb';

async function executeAdbCommand(command) {
    try {
        const { stdout } = await execPromise(`"${ADB_PATH}" ${command}`);
        return stdout.trim();
    } catch (error) {
        throw new Error(`Comando ADB fallito: ${error.message}`);
    }
}

async function resetUiAutomator() {
    try {
        // Stop current uiautomator
        await executeAdbCommand('shell am force-stop com.android.commands.uiautomator');
        await executeAdbCommand('shell am force-stop com.github.uiautomator');
        
        // Clear temp files
        const clearCommands = [
            'shell rm /sdcard/window_dump.xml',
            'shell rm /storage/emulated/0/window_dump.xml',
            'shell rm /data/local/tmp/window_dump.xml'
        ];

        for (const cmd of clearCommands) {
            try {
                await executeAdbCommand(cmd);
            } catch (error) {
                // Ignora errori di pulizia
            }
        }

        // Breve pausa
        await new Promise(resolve => setTimeout(resolve, 1000));
    } catch (error) {
        console.warn('Avviso durante reset uiautomator:', error.message);
    }
}

async function checkTextOnScreen(searchText) {
    try {
        console.log(`\nCercando il testo: "${searchText}"`);
        
        // Reset uiautomator
        console.log('Reset uiautomator...');
        await resetUiAutomator();
        
        // Create UI dump with error checking
        console.log('Creazione dump UI...');
        const dumpResult = await executeAdbCommand('shell uiautomator dump');
        console.log('Risultato dump:', dumpResult);

        // Try to find the dump file
        let dumpContent = null;
        const possiblePaths = [
            '/sdcard/window_dump.xml',
            '/storage/emulated/0/window_dump.xml',
            '/data/local/tmp/window_dump.xml'
        ];

        for (const path of possiblePaths) {
            try {
                dumpContent = await executeAdbCommand(`shell cat ${path}`);
                console.log(`File dump trovato in: ${path}`);
                break;
            } catch (error) {
                continue;
            }
        }

        if (!dumpContent) {
            throw new Error('File dump non trovato dopo la creazione');
        }

        // Search for text
        const textFound = dumpContent.toLowerCase().includes(searchText.toLowerCase());
        
        if (textFound) {
            console.log(`✅ Testo "${searchText}" trovato!`);
            return true;
        } else {
            console.log(`❌ Testo "${searchText}" non trovato.`);
            return false;
        }
        
    } catch (error) {
        console.error('Errore durante la ricerca:', error.message);
        return false;
    } finally {
        // Cleanup
        await resetUiAutomator();
    }
}

async function checkTextWithRetry(searchText, maxAttempts = 3, delayMs = 2000) {
    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
        console.log(`\nTentativo ${attempt}/${maxAttempts}`);
        
        if (await checkTextOnScreen(searchText)) {
            return true;
        }
        
        if (attempt < maxAttempts) {
            console.log(`Attendo ${delayMs}ms prima del prossimo tentativo...`);
            await new Promise(resolve => setTimeout(resolve, delayMs));
        }
    }
    
    console.log(`\nTesto non trovato dopo ${maxAttempts} tentativi.`);
    return false;
}

// Verifica connessione ADB
async function checkAdbConnection() {
    try {
        const devices = await executeAdbCommand('devices');
        const deviceList = devices.split('\n').slice(1).filter(line => line.trim());
        
        if (deviceList.length === 0) {
            throw new Error('Nessun dispositivo connesso');
        }
        console.log('Dispositivo connesso trovato:', deviceList[0]);
        return true;
    } catch (error) {
        console.error('Errore connessione ADB:', error.message);
        return false;
    }
}

// Main
const args = process.argv.slice(2);
const usage = `
Uso: node script.js <testo_da_cercare> [numero_tentativi] [delay_ms]
Esempio: node script.js "Cerca questo" 3 2000
`;

if (args.length === 0 || args[0] === '--help') {
    console.log(usage);
    process.exit(0);
}

const textToFind = args[0];
const attempts = parseInt(args[1]) || 3;
const delay = parseInt(args[2]) || 2000;

// Run
checkAdbConnection()
    .then(connected => {
        if (!connected) {
            process.exit(1);
        }
        return checkTextWithRetry(textToFind, attempts, delay);
    })
    .then(found => process.exit(found ? 0 : 1))
    .catch(error => {
        console.error('Errore fatale:', error);
        process.exit(1);
    });