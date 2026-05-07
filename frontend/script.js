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
    suggestionBox.className = 'docs-suggestion-box'; // We will style this in CSS

    // 1. The Suggestions
    if (errorData.suggestions.length === 0) {
        const noSugg = document.createElement('div');
        noSugg.className = 'suggestion-item disabled';
        noSugg.innerText = 'គ្មានពាក្យណែនាំទេ (No suggestions)';
        suggestionBox.appendChild(noSugg);
    } else {
        errorData.suggestions.forEach(word => {
            const item = document.createElement('div');
            item.className = 'suggestion-item';
            item.innerText = word;
            item.onclick = () => {
                // Fix the typo
                spanElement.innerText = word;
                spanElement.className = '';
                spanElement.style.color = 'black';
                suggestionBox.style.display = 'none';
            };
            suggestionBox.appendChild(item);
        });
    }

    // Add a subtle divider
    const divider = document.createElement('div');
    divider.className = 'suggestion-divider';
    suggestionBox.appendChild(divider);

    // 2. The "Ignore" Button (Just like Google Docs)
    const ignoreItem = document.createElement('div');
    ignoreItem.className = 'suggestion-item ignore-item';
    ignoreItem.innerText = 'រំលង (Ignore)';
    ignoreItem.onclick = () => {
        // Remove the red underline but keep the word
        spanElement.className = '';
        spanElement.style.color = 'black';
        suggestionBox.style.display = 'none';
    };
    suggestionBox.appendChild(ignoreItem);

    // 3. Position the box directly under the word
    const rect = spanElement.getBoundingClientRect();
    suggestionBox.style.left = `${rect.left + window.scrollX}px`;
    suggestionBox.style.top = `${rect.bottom + window.scrollY + 4}px`;
    suggestionBox.style.display = 'block';
}

document.addEventListener('click', () => {
    suggestionBox.style.display = 'none';
});