let currentLang = 'mr'; // बाय-डिफॉल्ट मराठी

const translations = {
    en: {
        subtitle: "Smart Cow Management System",
        searchBtn: "Search",
        lblBasic: "🐄 Basic Details",
        lblName: "Name:",
        lblBreed: "Breed:",
        lblAge: "Age:",
        lblYears: "years",
        lblPregnancy: "🤰 Pregnancy & AI Status",
        lblStatus: "Status:",
        lblAiDate: "AI Date:",
        lblCalvingDate: "Expected Calving:",
        lblDaysRem: "Days Remaining:",
        lblHealth: "💊 Health & History",
        lblSupplements: "Supplements:",
        lblTreatments: "Treatments:",
        lblVaccines: "Vaccinations:",
        lblTimelineTitle: "📋 Record Timeline",
        lblAddNewCow: "➕ Add New Cow Record",
        lblSaveBtn: "Save Cow Record"
    },
    mr: {
        subtitle: "स्मार्ट गोधन व्यवस्थापन प्रणाली",
        searchBtn: "शोध घ्या",
        lblBasic: "🐄 मूळ माहिती",
        lblName: "नाव:",
        lblBreed: "जात (ब्रीड):",
        lblAge: "वय:",
        lblYears: "वर्षे",
        lblPregnancy: "🤰 गाभण व भरवण (AI) माहिती",
        lblStatus: "स्थिती:",
        lblAiDate: "भरवल्याची तारीख (AI):",
        lblCalvingDate: "संभाव्य विण्याची तारीख:",
        lblDaysRem: "उरलेले दिवस:",
        lblHealth: "💊 उपचार व आरोग्य माहिती",
        lblSupplements: "पूरक आहार / सप्लीमेंट्स:",
        lblTreatments: "उपचाराचा इतिहास:",
        lblVaccines: "लसीकरणाचा इतिहास:",
        lblTimelineTitle: "📋 संपूर्ण घटनाक्रम (Timeline)",
        lblAddNewCow: "➕ नवीन गाईची नोंद करा",
        lblSaveBtn: "माहिती सेव्ह करा"
    }
};

function toggleLanguage() {
    currentLang = currentLang === 'en' ? 'mr' : 'en';
    const t = translations[currentLang];

    if (document.getElementById('appSubtitle')) document.getElementById('appSubtitle').innerText = t.subtitle;
    if (document.getElementById('searchBtn')) document.getElementById('searchBtn').innerText = t.searchBtn;
    if (document.getElementById('lblBasic')) document.getElementById('lblBasic').innerText = t.lblBasic;
    if (document.getElementById('lblName')) document.getElementById('lblName').innerText = t.lblName;
    if (document.getElementById('lblBreed')) document.getElementById('lblBreed').innerText = t.lblBreed;
    if (document.getElementById('lblAge')) document.getElementById('lblAge').innerText = t.lblAge;
    if (document.getElementById('lblYears')) document.getElementById('lblYears').innerText = t.lblYears;
    if (document.getElementById('lblPregnancy')) document.getElementById('lblPregnancy').innerText = t.lblPregnancy;
    if (document.getElementById('lblStatus')) document.getElementById('lblStatus').innerText = t.lblStatus;
    if (document.getElementById('lblAiDate')) document.getElementById('lblAiDate').innerText = t.lblAiDate;
    if (document.getElementById('lblCalvingDate')) document.getElementById('lblCalvingDate').innerText = t.lblCalvingDate;
    if (document.getElementById('lblDaysRem')) document.getElementById('lblDaysRem').innerText = t.lblDaysRem;
    if (document.getElementById('lblHealth')) document.getElementById('lblHealth').innerText = t.lblHealth;
    if (document.getElementById('lblSupplements')) document.getElementById('lblSupplements').innerText = t.lblSupplements;
    if (document.getElementById('lblTreatments')) document.getElementById('lblTreatments').innerText = t.lblTreatments;
    if (document.getElementById('lblVaccines')) document.getElementById('lblVaccines').innerText = t.lblVaccines;
    if (document.getElementById('lblTimelineTitle')) document.getElementById('lblTimelineTitle').innerText = t.lblTimelineTitle;
    if (document.getElementById('lblAddNewCow')) document.getElementById('lblAddNewCow').innerText = t.lblAddNewCow;
    if (document.getElementById('lblSaveBtn')) document.getElementById('lblSaveBtn').innerText = t.lblSaveBtn;
}

let currentSearchedCow = null;

// Search Cow
function searchCow() {
    const rawInput = document.getElementById('tagInput').value.trim();
    const tagNo = rawInput.toUpperCase().replace(/\s+/g, '-');
    const resultContainer = document.getElementById('resultContainer');
    const errorMsg = document.getElementById('errorMsg');

    if (!tagNo) {
        alert(currentLang === 'mr' ? "कृपया टॅग नंबर टाका!" : "Please enter a Tag Number!");
        return;
    }

    fetch(`/api/cow/${tagNo}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Cow record not found');
            }
            return response.json();
        })
        .then(data => {
            currentSearchedCow = data;
            errorMsg.style.display = 'none';
            resultContainer.style.display = 'block';

            document.getElementById('cowTagTitle').innerText = `Tag: ${data.tag_no}`;
            document.getElementById('cowName').innerText = data.name;
            document.getElementById('cowBreed').innerText = data.breed;
            document.getElementById('cowAge').innerText = data.age;

            document.getElementById('pregStatus').innerText = data.pregnancy_status;
            document.getElementById('aiDate').innerText = data.ai_date || 'N/A';
            document.getElementById('calvingDate').innerText = data.expected_calving_date || 'N/A';
            document.getElementById('daysRemaining').innerText = data.days_remaining !== 'N/A' ? `${data.days_remaining}` : 'N/A';

            document.getElementById('supplements').innerText = data.supplements || 'None';
            document.getElementById('treatments').innerText = data.treatment_history || 'None';
            document.getElementById('vaccines').innerText = data.vaccination_history || 'None';

            // Dynamic Timeline
            const timelineList = document.getElementById('cowTimeline');
            timelineList.innerHTML = '';

            if (data.ai_date && data.ai_date !== 'N/A') {
                timelineList.innerHTML += `<li>💉 <strong>AI Date:</strong> ${data.ai_date}</li>`;
            }
            if (data.expected_calving_date && data.expected_calving_date !== 'N/A') {
                timelineList.innerHTML += `<li>📅 <strong>Expected Calving:</strong> ${data.expected_calving_date}</li>`;
            }
            if (data.vaccination_history && data.vaccination_history !== 'None') {
                timelineList.innerHTML += `<li>🛡️ <strong>Vaccination:</strong> ${data.vaccination_history}</li>`;
            }
            if (data.treatment_history && data.treatment_history !== 'None') {
                timelineList.innerHTML += `<li>🩺 <strong>Treatment:</strong> ${data.treatment_history}</li>`;
            }
        })
        .catch(err => {
            currentSearchedCow = null;
            resultContainer.style.display = 'none';
            errorMsg.style.display = 'block';
            errorMsg.innerText = currentLang === 'mr' ? `❌ ${tagNo} टॅग नंबरचा डेटा सापडला नाही.` : `❌ No cow found with Tag Number: ${tagNo}`;
        });
}

// Save / Add Cow Record
function saveCow(event) {
    event.preventDefault();

    const tagInput = document.getElementById('addTagNo').value.trim();
    const formattedTag = tagInput.toUpperCase().replace(/\s+/g, '-');

    const cowData = {
        tag_no: formattedTag,
        name: document.getElementById('addName').value.trim(),
        breed: document.getElementById('addBreed').value.trim(),
        age: parseInt(document.getElementById('addAge').value) || 0,
        pregnancy_status: document.getElementById('addPregStatus').value,
        ai_date: document.getElementById('addAiDate').value || 'N/A',
        expected_calving_date: document.getElementById('addCalvingDate').value || 'N/A',
        supplements: document.getElementById('addSupplements').value.trim() || 'None',
        treatment_history: document.getElementById('addTreatments').value.trim() || 'None',
        vaccination_history: document.getElementById('addVaccines').value.trim() || 'None'
    };

    fetch('/api/cow/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(cowData)
    })
    .then(async response => {
        const data = await response.json();
        if (response.ok) {
            alert(currentLang === 'mr' ? "✅ नवीन गाईची नोंद यशस्वीपणे सेव्ह झाली!" : "✅ Cow record added successfully!");
            document.getElementById('addCowForm').reset();
            const recordsSec = document.getElementById('myRecordsSection');
            if (recordsSec && recordsSec.style.display !== 'none') {
                loadMyRecords();
            }
        } else {
            alert("❌ Save Error: " + (data.error || "Unknown error"));
        }
    })
    .catch(err => {
        console.error(err);
        alert("❌ Server Connection Failed: " + err.message);
    });
}

// Auto Calving Date Calculation (279 Days)
document.addEventListener('DOMContentLoaded', () => {
    const aiDateInput = document.getElementById('addAiDate');
    const calvingDateInput = document.getElementById('addCalvingDate');

    if (aiDateInput && calvingDateInput) {
        aiDateInput.addEventListener('change', function () {
            const selectedDateVal = this.value;
            if (selectedDateVal) {
                const aiDate = new Date(selectedDateVal);
                aiDate.setDate(aiDate.getDate() + 279);

                const year = aiDate.getFullYear();
                const month = String(aiDate.getMonth() + 1).padStart(2, '0');
                const day = String(aiDate.getDate()).padStart(2, '0');

                calvingDateInput.value = `${year}-${month}-${day}`;
            }
        });
    }
});

// Edit Form
function fillEditForm() {
    if (!currentSearchedCow) return;
    
    document.getElementById('addTagNo').value = currentSearchedCow.tag_no;
    document.getElementById('addName').value = currentSearchedCow.name;
    document.getElementById('addBreed').value = currentSearchedCow.breed;
    document.getElementById('addAge').value = currentSearchedCow.age;
    document.getElementById('addPregStatus').value = currentSearchedCow.pregnancy_status;
    document.getElementById('addAiDate').value = currentSearchedCow.ai_date !== 'N/A' ? currentSearchedCow.ai_date : '';
    document.getElementById('addCalvingDate').value = currentSearchedCow.expected_calving_date !== 'N/A' ? currentSearchedCow.expected_calving_date : '';
    document.getElementById('addSupplements').value = currentSearchedCow.supplements !== 'None' ? currentSearchedCow.supplements : '';
    document.getElementById('addTreatments').value = currentSearchedCow.treatment_history !== 'None' ? currentSearchedCow.treatment_history : '';
    document.getElementById('addVaccines').value = currentSearchedCow.vaccination_history !== 'None' ? currentSearchedCow.vaccination_history : '';

    window.scrollTo({ top: document.querySelector('.add-cow-section').offsetTop, behavior: 'smooth' });
    alert("माहिती फॉर्ममध्ये लोड झाली आहे. बदल करून 'Save Record' वर क्लिक करा!");
}

// Delete Record
function deleteCow() {
    const tag = (currentSearchedCow && currentSearchedCow.tag_no) 
                ? currentSearchedCow.tag_no 
                : document.getElementById('tagInput').value.trim();

    if (!tag) {
        alert("डिलिट करण्यासाठी टॅग नंबर सापडला नाही!");
        return;
    }

    if (confirm(`तुम्हाला नक्की ${tag} ची नोंद डिलीट करायची आहे का?`)) {
        fetch(`/api/cow/delete/${encodeURIComponent(tag)}`, { method: 'DELETE' })
            .then(async res => {
                const isJson = res.headers.get('content-type')?.includes('application/json');
                const data = isJson ? await res.json() : null;

                if (!res.ok) {
                    const error = (data && data.error) || `Server Error (${res.status}).`;
                    return Promise.reject(error);
                }
                return data;
            })
            .then(data => {
                alert("✅ " + data.message);
                document.getElementById('resultContainer').style.display = 'none';
                currentSearchedCow = null;
                document.getElementById('tagInput').value = '';

                const recordsSec = document.getElementById('myRecordsSection');
                if (recordsSec && recordsSec.style.display !== 'none') {
                    loadMyRecords();
                }
            })
            .catch(err => {
                console.error(err);
                alert("❌ " + err);
            });
    }
}

// Load All Cows List
function loadMyRecords() {
    fetch('/api/cows/all')
        .then(res => res.json())
        .then(cows => {
            const tbody = document.getElementById('recordsTableBody');
            const section = document.getElementById('myRecordsSection');
            tbody.innerHTML = '';

            if (!cows || cows.length === 0) {
                tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; padding: 15px;">कोणतीही नोंद सापडली नाही.</td></tr>`;
            } else {
                cows.forEach(cow => {
                    tbody.innerHTML += `
                        <tr style="border-bottom: 1px solid #e2e8f0;">
                            <td style="padding: 10px;"><strong>${cow.tag_no}</strong></td>
                            <td style="padding: 10px;">${cow.name || '-'}</td>
                            <td style="padding: 10px;">${cow.breed || '-'}</td>
                            <td style="padding: 10px;">${cow.pregnancy_status}</td>
                            <td style="padding: 10px;">
                                <button onclick="viewCowFromList('${cow.tag_no}')" style="background: #3498db; color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer;">🔍 View</button>
                            </td>
                        </tr>
                    `;
                });
            }
            section.style.display = 'block';
            section.scrollIntoView({ behavior: 'smooth' });
        })
        .catch(err => alert("डेटा लोड करताना एरर आला: " + err));
}

function viewCowFromList(tagNo) {
    document.getElementById('tagInput').value = tagNo;
    searchCow();
}