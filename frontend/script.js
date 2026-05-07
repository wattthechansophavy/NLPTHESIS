const checkBtn = document.getElementById('checkBtn');
const inputText = document.getElementById('inputText');
const resultArea = document.getElementById('resultArea');
const xrayArea = document.getElementById('xrayArea');
const suggestionBox = document.getElementById('suggestionBox');

let currentErrors = [];

checkBtn.addEventListener('click', async () => {
    const text = inputText.value.trim();
    if (!text) return;

    checkBtn.innerText = "កំពុងពិនិត្យ... (Checking...)";
    checkBtn.disabled = true;

    try {
        const response = await fetch('http://127.0.0.1:8000/check_spelling', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: text })
        });
        
        const data = await response.json();
        
        // --- SAFETY CHECK ---
        if (!data.annotated_text) {
            console.error("Python sent the wrong data format:", data);
            throw new Error("Backend did not return 'annotated_text'. Did you save main.py?");
        }
        // --------------------

        renderAnnotatedText(data.annotated_text);

    } catch (error) {
        console.error("The REAL JavaScript error is:", error);
        resultArea.innerHTML = `<p style="color:red;">JavaScript Error: ${error.message}</p>`;
    
    } finally {
        checkBtn.innerText = "ពិនិត្យអក្ខរាវិរុទ្ធ (Check Spelling)";
        checkBtn.disabled = false;
    }
});

function renderAnnotatedText(annotatedArray) {
    let htmlOutput = "";
    let errorIndex = 0;
    let errorsData = [];

    // Build the text left-to-right to prevent the "Global Replace" bug
    annotatedArray.forEach(item => {
        if (item.is_typo) {
            htmlOutput += `<span class="typo" data-index="${errorIndex}">${item.text}</span>`;
            
            // Format data so the purple popup box still works
            errorsData.push({ typo: item.text, suggestions: item.suggestions });
            errorIndex++;
        } else {
            htmlOutput += item.text;
        }
    });

    resultArea.innerHTML = htmlOutput;

    // Attach click events for the purple popup
    document.querySelectorAll('.typo').forEach(span => {
        span.addEventListener('click', (e) => {
            e.stopPropagation();
            const idx = e.target.getAttribute('data-index');
            showSuggestions(e.target, errorsData[idx]);
        });
    });
}

function showSuggestions(spanElement, errorData) {
    suggestionBox.innerHTML = '';

    // 1. Build the Header
    const header = document.createElement('div');
    header.className = 'popup-header';
    header.innerHTML = `
        <div class="popup-header-title">
            <span class="popup-icon">ក</span>
            <span>កំហុសអក្ខរាវិរុទ្ធ</span>
        </div>
        <button class="close-btn" onclick="document.getElementById('suggestionBox').style.display='none'">X</button>
    `;
    suggestionBox.appendChild(header);

    // 2. Build the Body
    const body = document.createElement('div');
    body.className = 'popup-body';
    
    // The red crossed-out word
    const wrongWord = document.createElement('div');
    wrongWord.className = 'wrong-word-display';
    wrongWord.innerText = errorData.typo;
    body.appendChild(wrongWord);

    // The Grid of Purple Buttons
    const grid = document.createElement('div');
    grid.className = 'suggestion-grid';

    if (errorData.suggestions.length === 0) {
        grid.innerHTML = '<span style="color:#888;">គ្មានពាក្យណែនាំទេ (No suggestions)</span>';
    } else {
        errorData.suggestions.forEach(word => {
            const btn = document.createElement('button');
            btn.className = 'suggestion-btn';
            btn.innerText = word;
            btn.onclick = () => {
                // Replace the text and remove the red underline!
                spanElement.innerText = word;
                spanElement.className = '';
                spanElement.style.color = 'black';
                suggestionBox.style.display = 'none';
            };
            grid.appendChild(btn);
        });
    }
    
    body.appendChild(grid);
    suggestionBox.appendChild(body);

    // 3. Build the Footer
    const footer = document.createElement('div');
    footer.className = 'popup-footer';
    footer.innerText = 'ភាសាខ្មែរ (Khmerlang)';
    suggestionBox.appendChild(footer);

    // Position the box right below the clicked word
    const rect = spanElement.getBoundingClientRect();
    suggestionBox.style.left = `${rect.left + window.scrollX}px`;
    suggestionBox.style.top = `${rect.bottom + window.scrollY + 5}px`;
    suggestionBox.style.display = 'block';
}

document.addEventListener('click', () => {
    suggestionBox.style.display = 'none';
});