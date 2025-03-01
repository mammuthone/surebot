const { exec } = require('child_process');
const util = require('util');
const execPromise = util.promisify(exec);
const fs = require('fs').promises;
const path = require('path');

const ADB_PATH = 'adb';

// Possibili percorsi per il dump
const DUMP_PATHS = [
    '/sdcard',
    '/storage/emulated/0',
    '/data/local/tmp'
];

async function findWritablePath() {
    for (const basePath of DUMP_PATHS) {
        try {
            // Prova a scrivere un file di test
            const testFile = 'test_write_access';
            await execPromise(`${ADB_PATH} shell touch ${basePath}/${testFile}`);
            await execPromise(`${ADB_PATH} shell rm ${basePath}/${testFile}`);
            console.log(`✓ Trovato percorso scrivibile: ${basePath}`);
            return basePath;
        } catch (error) {
            console.log(`× Percorso non scrivibile: ${basePath}`);
            continue;
        }
    }
    throw new Error('Nessun percorso scrivibile trovato');
}

async function dumpUIHierarchy(outputDir) {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const baseFileName = `ui_dump_${timestamp}`;
    
    try {
        // Crea directory se non esiste
        await fs.mkdir(outputDir, { recursive: true });
        
        console.log('Raccolta informazioni UI in corso...\n');

        // Trova un percorso scrivibile
        const writablePath = await findWritablePath();
        
        // 1. UI Automator dump con verifica
        console.log('📱 Generando dump XML della UI...');
        const xmlPath = `${writablePath}/${baseFileName}.xml`;
        const dumpResult = await execPromise(`${ADB_PATH} shell uiautomator dump ${xmlPath}`);
        console.log('Risultato dump:', dumpResult.stdout);
        
        // Verifica che il file esista prima di procedere
        const checkFile = await execPromise(`${ADB_PATH} shell ls ${xmlPath}`);
        console.log(`File dump creato: ${checkFile.stdout}`);
        
        // Pull del file
        await execPromise(`${ADB_PATH} pull ${xmlPath} ${path.join(outputDir, baseFileName + '.xml')}`);
        await execPromise(`${ADB_PATH} shell rm ${xmlPath}`);

        // 2. Window Manager state
        console.log('🪟 Raccogliendo stato Window Manager...');
        const { stdout: windowInfo } = await execPromise(`${ADB_PATH} shell dumpsys window windows`);
        await fs.writeFile(path.join(outputDir, baseFileName + '_windows.txt'), windowInfo);

        // 3. Activity Manager state
        console.log('📚 Raccogliendo stato Activity Manager...');
        const { stdout: activityInfo } = await execPromise(`${ADB_PATH} shell dumpsys activity activities`);
        await fs.writeFile(path.join(outputDir, baseFileName + '_activities.txt'), activityInfo);

        // 4. View hierarchy tramite dumpsys
        console.log('👁️ Raccogliendo gerarchia view...');
        const { stdout: viewInfo } = await execPromise(`${ADB_PATH} shell dumpsys activity top`);
        await fs.writeFile(path.join(outputDir, baseFileName + '_view_hierarchy.txt'), viewInfo);

        console.log('\n✅ Dump UI completato con successo!');
        console.log(`\nFile salvati in ${outputDir}:`);
        console.log(`- UI XML: ${baseFileName}.xml`);
        console.log(`- Window Info: ${baseFileName}_windows.txt`);
        console.log(`- Activity Info: ${baseFileName}_activities.txt`);
        console.log(`- View Hierarchy: ${baseFileName}_view_hierarchy.txt`);

    } catch (error) {
        console.error('❌ Errore durante il dump:', error.message);
        
        // Suggerimenti per il debug
        console.error('\nSuggerimenti per la risoluzione:');
        console.error('1. Verifica che le Opzioni Sviluppatore siano attive');
        console.error('2. Prova questi comandi:');
        console.error('   adb kill-server && adb start-server');
        console.error('   adb shell settings put global development_settings_enabled 1');
        console.error('3. Verifica i permessi con: adb shell ls -l /sdcard/');
        throw error;
    }
}

// Gestione argomenti
const args = process.argv.slice(2);
const usage = `
Uso: node script.js [directory_output]
Se non specificata, la directory di output sarà './ui_dumps'

Esempio: 
  node script.js ./my_ui_dumps
`;

if (args.includes('--help') || args.includes('-h')) {
    console.log(usage);
    process.exit(0);
}

const outputDir = args[0] || './ui_dumps';

// Esegui il dump
dumpUIHierarchy(outputDir)
    .then(() => process.exit(0))
    .catch(error => {
        console.error('\n❌ Errore fatale:', error);
        process.exit(1);
    });