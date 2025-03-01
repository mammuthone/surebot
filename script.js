const { exec } = require('child_process');
const util = require('util');
const execPromise = util.promisify(exec);
const path = require('path');
const commandLineArgs = require('command-line-args');
const nodemailer = require('nodemailer');
const fs = require('fs').promises;
// Configura il path di ADB in base al tuo sistema
// Modifica questo path con il percorso corretto di adb sul tuo sistema
const ADB_PATH = '/Users/igor/Library/Android/sdk/platform-tools/adb';  // macOS/Linux

const optionDefinitions = [
    { name: 'sport', alias: 's', type: String },
    // { name: 'team1', alias: 't1', type: String, multiple: true, defaultOption: true },
    { name: 'team1', type: String },
    { name: 'team2', type: String },
  ]

async function takeScreenshot() {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const filename = `screenshot-${timestamp}.png`;
    const localPath = path.join(__dirname, filename);

    try {
        // Cattura screenshot sul device
        console.log('Acquisizione screenshot...');
        await execPromise(`"${config.adbPath}" shell screencap -p /sdcard/${filename}`);

        // Trasferisci sul computer
        console.log('Trasferimento file...');
        await execPromise(`"${config.adbPath}" pull /sdcard/${filename} ${localPath}`);

        // Rimuovi dal device
        await execPromise(`"${config.adbPath}" shell rm /sdcard/${filename}`);

        return localPath;
    } catch (error) {
        throw new Error(`Errore screenshot: ${error.message}`);
    }
}

const config = {
    adbPath: '/Users/igor/Library/Android/sdk/platform-tools/adb',
    email: {
        from: 'igorino80@gmail.com',
        to: 'igorino80@gmail.com',
        subject: 'Screenshot from device',
        // Per Gmail devi usare una password per le app
        // https://myaccount.google.com/apppasswords
        auth: {
            user: 'igorino80@gmail.com',
            pass: 'rwklpbadqvkqpwpp'
        }
    }
};

async function sendEmail(screenshotPath) {
    // Configura il trasporto email
    const transporter = nodemailer.createTransport({
        service: 'gmail',
        auth: config.email.auth
    });

    try {
        // Leggi il file
        const attachment = await fs.readFile(screenshotPath);

        // Prepara l'email
        const mailOptions = {
            from: config.email.from,
            to: config.email.to,
            subject: config.email.subject,
            text: 'Screenshot allegato.',
            attachments: [{
                filename: path.basename(screenshotPath),
                content: attachment
            }]
        };

        // Invia
        console.log('Invio email...');
        await transporter.sendMail(mailOptions);
        console.log('Email inviata con successo!');

        // Pulizia file locale
        await fs.unlink(screenshotPath);
    } catch (error) {
        throw new Error(`Errore email: ${error.message}`);
    }
}

const options = commandLineArgs(optionDefinitions)

async function runAdbCommands() {
    try {
        
        // Verifica che ADB sia accessibile
        console.log('Verifico ADB...');
        try {
            await execPromise(`"${ADB_PATH}" devices`);
        } catch (error) {
            throw new Error(`ADB non trovato nel path: ${ADB_PATH}. \nVerifica il percorso corretto di ADB nel tuo sistema.`);
        }
        
        // Apri l'app
        console.log('Avvio applicazione...');
        await execPromise(`"${ADB_PATH}" shell monkey -p com.mobenga.sisal 1`);
        
        // Attendi 5 secondi
        console.log('Attendo 15 secondi...');
        await new Promise(resolve => setTimeout(resolve, 15000));
        

        // Esegui il tap
        console.log('Eseguo tap sulle coordinate (890,1280)...');
        await execPromise(`"${ADB_PATH}" shell input tap 890 1280`);
        await new Promise(resolve => setTimeout(resolve, 1000));
        await execPromise(`"${ADB_PATH}" shell input tap 230 480`);
        await new Promise(resolve => setTimeout(resolve, 1000));

        const match = `${options.team1} ${options.team2}`
        await execPromise(`"${ADB_PATH}" shell input text ${match}`);
        await execPromise(`"${ADB_PATH}" shell input tap 570 2140`);
          // spazio singolo
        await execPromise(`"${ADB_PATH}" shell input text ${options.team2}`);
        await new Promise(resolve => setTimeout(resolve, 1000));
        await execPromise(`"${ADB_PATH}" shell input keyevent 66`);
        await new Promise(resolve => setTimeout(resolve, 1000));
        await execPromise(`"${ADB_PATH}" shell input tap 470 790`);
        await new Promise(resolve => setTimeout(resolve, 15000));
        
    
        const screenshotPath = await takeScreenshot();
        await sendEmail(screenshotPath);
        
        
        
        await execPromise(`"${ADB_PATH}" shell am force-stop com.mobenga.sisal`);
        
        console.log('Sequenza completata con successo!');
    } catch (error) {
        console.error('Errore durante l\'esecuzione:', error.message);
    }
}

// Esegui lo script
runAdbCommands();