const fs = require('fs');
const path = require('path');
const archiver = require('archiver');

async function createZip() {
    const outputPath = path.join(__dirname, '..', 'anonymous-app-final.zip');
    const output = fs.createWriteStream(outputPath);
    const archive = archiver('zip', {
        zlib: { level: 9 } // Máxima compressão
    });

    output.on('close', function() {
        console.log(`✅ ZIP criado com sucesso: ${outputPath}`);
        console.log(`📦 Tamanho total: ${archive.pointer()} bytes`);
    });

    archive.on('error', function(err) {
        throw err;
    });

    archive.pipe(output);

    // Adicionar todos os arquivos do projeto, exceto node_modules e outros desnecessários
    const excludePatterns = [
        'node_modules',
        '.git',
        'dist',
        '__pycache__',
        '.pytest_cache',
        'venv',
        '.env',
        '*.log',
        '.DS_Store',
        'Thumbs.db',
        'anonymous-app-final.zip'
    ];

    function shouldExclude(filePath) {
        return excludePatterns.some(pattern => {
            if (pattern.includes('*')) {
                return filePath.includes(pattern.replace('*', ''));
            }
            return filePath.includes(pattern);
        });
    }

    function addDirectory(dirPath, zipPath = '') {
        const items = fs.readdirSync(dirPath);
        
        items.forEach(item => {
            const fullPath = path.join(dirPath, item);
            const relativePath = zipPath ? path.join(zipPath, item) : item;
            
            if (shouldExclude(fullPath)) {
                return;
            }
            
            const stat = fs.statSync(fullPath);
            
            if (stat.isDirectory()) {
                addDirectory(fullPath, relativePath);
            } else {
                archive.file(fullPath, { name: relativePath });
            }
        });
    }

    // Adicionar todos os arquivos do projeto
    addDirectory(path.join(__dirname, '..'));

    await archive.finalize();
}

createZip().catch(console.error);
