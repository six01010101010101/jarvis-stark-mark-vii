const { app, BrowserWindow } = require('electron');
const path = require('path');
const fs = require('fs');

class FileService {
    strictSafeFilename(userInputName, defaultTitle) {
        let safeName = userInputName.replace(/[\/\\:*?"<>|]/g, '_');

        safeName = safeName.replace(/^\.+/, '');

        const encoder = new TextEncoder();
        const decoder = new TextDecoder("utf-8");
        let buf = encoder.encode(safeName);

        if (buf.length > 255) {
            safeName = decoder.decode(buf.slice(0, 255));
        }

        return safeName || defaultTitle;
    }

    generatePdfFromEmbeddedHtml(embeddedHtmlContent) {
        return new Promise(async (resolve, reject) => {
            let workerWindow = new BrowserWindow({
                show: false
            });

            const tempFilePath = path.join(app.getPath('temp'), `worker_temp_${Date.now()}.html`);
            await fs.promises.writeFile(tempFilePath, embeddedHtmlContent, 'utf-8');

            workerWindow.loadURL(`file://${tempFilePath}`);

            workerWindow.webContents.on('did-fail-load', (event, errorCode, errorDescription, validatedURL, isMainFrame) => {
                if (isMainFrame) {
                    reject(new Error(`Failed to load HTML: ${errorDescription} (${errorCode})`));
                    if (workerWindow) {
                        workerWindow.destroy();
                        workerWindow = null;
                    }
                }
            });

            workerWindow.webContents.on('did-finish-load', async () => {
                try {
                    const pdfBuffer = await workerWindow.webContents.printToPDF({
                        printBackground: true,
                        pageSize: 'A4',
                        marginsType: 1
                    });

                    resolve(pdfBuffer);
                } catch (err) {
                    reject(err);
                } finally {
                    if (workerWindow) {
                        workerWindow.destroy();
                        workerWindow = null;
                    }
                }
            });
        });
    }
}

module.exports = FileService;
