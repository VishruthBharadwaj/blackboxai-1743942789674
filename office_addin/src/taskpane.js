Office.onReady(() => {
    // Load classifications from server
    loadClassifications();
    
    // Set up event listeners
    document.getElementById('apply-btn').addEventListener('click', applyClassification);
    
    // Check for sensitive content
    checkSensitiveContent();
});

async function loadClassifications() {
    try {
        const response = await fetch('http://localhost:5000/api/classifications');
        const classifications = await response.json();
        
        const container = document.getElementById('classification-options');
        classifications.forEach(cls => {
            const div = document.createElement('div');
            div.className = 'flex items-center';
            div.innerHTML = `
                <input type="radio" id="cls-${cls.id}" name="classification" value="${cls.id}" 
                       class="h-4 w-4 text-blue-600 focus:ring-blue-500">
                <label for="cls-${cls.id}" class="ml-2 block text-sm text-gray-700">
                    <span class="inline-block h-3 w-3 rounded-full mr-1" style="background-color: ${cls.color}"></span>
                    ${cls.name}
                </label>
            `;
            container.appendChild(div);
        });
    } catch (error) {
        showMessage('Error loading classifications', 'error');
    }
}

async function checkSensitiveContent() {
    try {
        const content = await getDocumentContent();
        const response = await fetch('http://localhost:5000/api/ai_classify', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content })
        });
        
        const result = await response.json();
        if (result.classification_id) {
            document.getElementById('sensitivity-warning').classList.remove('hidden');
            // Auto-select suggested classification
            const radio = document.querySelector(`input[value="${result.classification_id}"]`);
            if (radio) radio.checked = true;
        }
    } catch (error) {
        console.error('AI check failed:', error);
    }
}

async function getDocumentContent() {
    return new Promise((resolve) => {
        Office.context.document.getFileAsync(Office.FileType.Text, {}, (result) => {
            if (result.status === Office.AsyncResultStatus.Succeeded) {
                const file = result.value;
                const sliceCount = Math.min(file.sliceCount, 3); // Only check first few slices
                let content = '';
                
                const processSlice = (index) => {
                    file.getSliceAsync(index, (sliceResult) => {
                        if (sliceResult.status === Office.AsyncResultStatus.Succeeded) {
                            content += sliceResult.value.data;
                            if (index < sliceCount - 1) {
                                processSlice(index + 1);
                            } else {
                                file.closeAsync();
                                resolve(content);
                            }
                        }
                    });
                };
                
                processSlice(0);
            } else {
                resolve('');
            }
        });
    });
}

async function applyClassification() {
    const selected = document.querySelector('input[name="classification"]:checked');
    if (!selected) {
        showMessage('Please select a classification', 'error');
        return;
    }
    
    try {
        const classificationId = selected.value;
        const classification = await getClassificationDetails(classificationId);
        
        // Add footer with classification
        await addFooter(classification);
        
        // Log the action
        await logClassification(classificationId);
        
        showMessage('Classification applied successfully!', 'success');
    } catch (error) {
        showMessage('Failed to apply classification', 'error');
        console.error(error);
    }
}

async function getClassificationDetails(id) {
    const response = await fetch(`http://localhost:5000/api/classifications/${id}`);
    return await response.json();
}

async function addFooter(classification) {
    return new Promise((resolve) => {
        Office.context.document.setSelectedDataAsync(
            `\n\nClassification: ${classification.name} | User: ${Office.context.mailbox.userProfile.emailAddress}`,
            { coercionType: Office.CoercionType.Text },
            (result) => {
                if (result.status === Office.AsyncResultStatus.Succeeded) {
                    resolve();
                } else {
                    throw new Error('Failed to add footer');
                }
            }
        );
    });
}

async function logClassification(classificationId) {
    const response = await fetch('http://localhost:5000/api/log_document', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            filename: await getDocumentName(),
            path: 'office_document',
            classification_id: classificationId,
            user: Office.context.mailbox.userProfile.emailAddress,
            action: 'classified'
        })
    });
    
    if (!response.ok) {
        throw new Error('Failed to log classification');
    }
}

async function getDocumentName() {
    return new Promise((resolve) => {
        Office.context.document.getFilePropertiesAsync((result) => {
            if (result.status === Office.AsyncResultStatus.Succeeded) {
                resolve(result.value.url ? result.value.url.split('/').pop() : 'Untitled');
            } else {
                resolve('Untitled');
            }
        });
    });
}

function showMessage(text, type) {
    const element = document.getElementById('status-message');
    element.textContent = text;
    element.className = `mt-4 p-3 rounded ${
        type === 'error' ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'
    }`;
    element.classList.remove('hidden');
    
    setTimeout(() => {
        element.classList.add('hidden');
    }, 5000);
}