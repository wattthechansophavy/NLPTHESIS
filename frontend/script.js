const checkBtn = document.getElementById('checkBtn');
const inputText = document.getElementById('inputText');
const resultArea = document.getElementById('resultArea');
const suggestionBox = document.getElementById('suggestionBox');
const copyBtn = document.getElementById('copyBtn');

// 1. The Main Check Button Trigger
checkBtn.addEventListener('click', async () => {
    const text = inputText.value.trim();
    if (!text) return;

    // Update UI to loading state
    checkBtn.innerText = "កំពុងពិនិត្យ... (Checking...)";
    checkBtn.disabled = true;
    copyBtn.disabled = true; // Keep copy disabled while loading

    try {
        const response = await fetch('http://127.0.0.1:8000/check_spelling', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: text })
        });
        
        const data = await response.json();
        
        if (!data.annotated_text) {
            console.error("Python sent the wrong data format:", data);
            throw new Error("Backend did not return 'annotated_text'. Did you save main.py?");
        }

        // Render the text and turn on the Copy button!
        renderAnnotatedText(data.annotated_text);
        copyBtn.disabled = false; 

    } catch (error) {
        console.error("The REAL JavaScript error is:", error);
        resultArea.innerHTML = `<p style="color:red;">JavaScript Error: ${error.message}</p>`;
    } finally {
        // Restore the check button
        checkBtn.innerText = "ពិនិត្យអក្ខរាវិរុទ្ធ (Check Spelling)";
        checkBtn.disabled = false;
    }
});

// 2. Rendering the Output
function renderAnnotatedText(annotatedArray) {
    let htmlOutput = "";
    let errorIndex = 0;
    let errorsData = [];

    // Build the text left-to-right
    annotatedArray.forEach(item => {
        if (item.is_typo) {
            htmlOutput += `<span class="typo" data-index="${errorIndex}">${item.text}</span>`;
            errorsData.push({ typo: item.text, suggestions: item.suggestions });
            errorIndex++;
        } else {
            htmlOutput += item.text;
        }
    });

    resultArea.innerHTML = htmlOutput;

    // Attach click events to the orange typos
    document.querySelectorAll('.typo').forEach(span => {
        span.addEventListener('click', (e) => {
            e.stopPropagation();
            const idx = e.target.getAttribute('data-index');
            showSuggestions(e.target, errorsData[idx]);
        });
    });
}

// 3. The Dropdown UI
function showSuggestions(spanElement, errorData) {
    suggestionBox.innerHTML = '';
    suggestionBox.className = 'docs-suggestion-box';

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
                // Apply the fix
                spanElement.innerText = word;
                spanElement.className = ''; 
                spanElement.style.color = 'inherit'; // Matches the dark brown text
                suggestionBox.style.display = 'none';
            };
            suggestionBox.appendChild(item);
        });
    }

    // Divider
    const divider = document.createElement('div');
    divider.className = 'suggestion-divider';
    suggestionBox.appendChild(divider);

    // Ignore Button
    const ignoreItem = document.createElement('div');
    ignoreItem.className = 'suggestion-item ignore-item';
    ignoreItem.innerText = 'រំលង (Ignore)';
    ignoreItem.onclick = () => {
        spanElement.className = '';
        spanElement.style.color = 'inherit';
        suggestionBox.style.display = 'none';
    };
    suggestionBox.appendChild(ignoreItem);

    // Position the dropdown box directly under the specific word
    const rect = spanElement.getBoundingClientRect();
    suggestionBox.style.left = `${rect.left + window.scrollX}px`;
    suggestionBox.style.top = `${rect.bottom + window.scrollY + 4}px`;
    suggestionBox.style.display = 'block';
}

// 4. The Copy Button Logic
copyBtn.addEventListener('click', () => {
    // Extract raw text, ignoring HTML tags
    const textToCopy = resultArea.innerText; 
    
    navigator.clipboard.writeText(textToCopy).then(() => {
        const originalText = copyBtn.innerText;
        copyBtn.innerText = 'បានចម្លង! (Copied!)';
        copyBtn.style.backgroundColor = '#4CAF50'; 
        copyBtn.style.color = 'white';
        copyBtn.style.borderColor = '#4CAF50';
        
        // Revert back to original styling after 2 seconds
        setTimeout(() => {
            copyBtn.innerText = originalText;
            copyBtn.style.backgroundColor = '';
            copyBtn.style.color = 'var(--text-dark)';
            copyBtn.style.borderColor = 'var(--primary-btn)';
        }, 2000);
    });
});

// Hide suggestion box if the user clicks anywhere else on the page
document.addEventListener('click', () => {
    suggestionBox.style.display = 'none';
});