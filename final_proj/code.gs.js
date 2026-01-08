/************** CONFIG **************/

const TOKEN = 'ТОКЕН ТГ БОТА';
const SHEET_ID = 'ID Листа Google Docs'; // Возьми из URL таблицы
const OPENAI_KEY = 'Ключ API OpenAI';

// Системный промпт GPT
const SYSTEM_PROMPT = `
Ты — сотрудник ресторана и проводишь порос клиентов клиентов ресторана.
Ты строго задаёшь вопросы из списка и можешь формулировать уточняющие вопросы, если ответ неполный.
Все вопросы, которые ты задаешь, касаются только ресторана, его работы и его внутреннего пространства.
Не задавй вопросы клиенту? которые не могут иметь отношения к ресторану.
Всегда возвращайся к вопросам о ресторане, если клиент пишет что-то отвелченное.
Твоя задача — вести дружелюбный и профессиональный диалог с клиентом, задавать вопросы по очереди, 
собирать ответы и анализировать их.
Обращайся по имени клиента, задавай вопросы по одному, формулируй уточняющие вопросы при необходимости.
После того как все ответы собраны, выдаешь строго в формате:
Сегментация: <краткая сегментация клиента>
Гипотезы: 1. ... 2. ... 3. ...
Никаких дополнительных приветствий, уточнений, вопросов или текстов. Только сегментация и гипотезы.
`;

// Вопросы кастдева (не включая имя и телефон)
const QUESTIONS = [
"Как часто Вы бываете в нашем ресторане ПИВOFF?",
"Какой средний чек на человека получается у Вас при посещении нашего ресторана?",
"Что Вам больше всего нравится в нашем ресторане ПИВOFF?",
"Что Вам меньше всего нравится в нашем ресторане ПИВOFF?",
"Какие дополнительные блюда Вы хотели бы видеть в меню?",
"Что сделало бы Ваш визит идеальным?"
];

// ================== doPost ==================
function doPost(e) {
const output = HtmlService.createHtmlOutput("");

try {
if (!e || !e.postData || !e.postData.contents) return output;

const data = JSON.parse(e.postData.contents);

// логируем входящие данные
SpreadsheetApp.openById(SHEET_ID)
.getSheetByName("Debug")
.appendRow([new Date(), JSON.stringify(data)]);

// обработка сообщений
handleMessageAsync(data);

} catch(err) {
SpreadsheetApp.openById(SHEET_ID)
.getSheetByName("Debug")
.appendRow([new Date(), "Ошибка doPost: " + err]);
}

return output; // мгновенный ответ Telegram
}

// ================== Обработка сообщений ==================
function handleMessageAsync(data) {
if (!data.message || !data.message.text) return;

const chatId = data.message.chat.id;
const text = data.message.text.trim();

const sheet = SpreadsheetApp.openById(SHEET_ID).getSheetByName("Responses");

// ищем или создаём строку для пользователя
const row = findOrCreateRow(sheet, chatId);

let progress = sheet.getRange(row, 3).getValue() || 0; // прогресс по вопросам
let awaitingClarification = sheet.getRange(row, 4 + QUESTIONS.length + 1).getValue() || false;

// старт опроса
if (text === "/start") {
progress = 0;
sheet.getRange(row, 3).setValue(progress);
sheet.getRange(row, 4 + QUESTIONS.length + 1).setValue(false); // нет ожидания уточнения
sendTelegramMessage(chatId, "Добрый день! Пройдите небольшой опрос и получите 1000 бонусных балоов в ресторане ПИВOFF!Как Вас зовут?");
sendTelegramMessage(chatId, "Представьтесь, пожалуста!");
return;
}

// имя клиента
if (progress === 0) {
sheet.getRange(row, 4).setValue(text); // колонка 4 — имя
progress++;
sheet.getRange(row, 3).setValue(progress);
sendTelegramMessage(chatId, "Спасибо! Теперь, пожалуйста, введите Ваш номер телефона:");
return;
}

// телефон
if (progress === 1) {
sheet.getRange(row, 5).setValue(text); // колонка 5 — телефон
progress++;
sheet.getRange(row, 3).setValue(progress);
sendTelegramMessage(chatId, "Спасибо! Начнем опрос.");
sendTelegramMessage(chatId, QUESTIONS[progress - 2]);
return;
}

// обработка вопросов кастдева
if (progress >= 2) {
const questionIndex = progress - 2;
const clientName = sheet.getRange(row, 4).getValue(); // <- берём имя клиента

// если бот ожидает уточнение
if (awaitingClarification) {
sheet.getRange(row, 6 + questionIndex).setValue(text); // уточнение
sheet.getRange(row, 4 + QUESTIONS.length + 1).setValue(false); // сняли ожидание
progress++;
sheet.getRange(row, 3).setValue(progress);
if (progress - 2 < QUESTIONS.length) {
sendTelegramMessage(chatId, QUESTIONS[progress - 2]);
} else {
finishSurvey(chatId, row);
}
return;
}

// сохраняем основной ответ
sheet.getRange(row, 6 + questionIndex).setValue(text);

// проверяем, нужен ли уточняющий вопрос
const needClarification = callOpenAI(
`Ответ клиента на вопрос "${QUESTIONS[questionIndex]}" был: "${text}". Нужно ли уточнить ответ для точного анализа? Ответь коротко "да" или "нет".`
);

if (needClarification.toLowerCase().includes("да")) {
const clarification = callOpenAI(
`Имя клиента: ${clientName}\nСформулируй короткий уточняющий вопрос по теме: "${text}"`
);
sendTelegramMessage(chatId, clarification);
sheet.getRange(row, 4 + QUESTIONS.length + 1).setValue(true); // ставим флаг ожидания уточнения
return;
}

// переходим к следующему вопросу
progress++;
sheet.getRange(row, 3).setValue(progress);
if (progress - 2 < QUESTIONS.length) {
sendTelegramMessage(chatId, QUESTIONS[progress - 2]);
} else {
finishSurvey(chatId, row);
}
}
}

function finishSurvey(chatId, row) {
const sheet = SpreadsheetApp.openById(SHEET_ID);
const responseSheet = sheet.getSheetByName("Responses");
const analysisSheet = sheet.getSheetByName("Analysis") || sheet.insertSheet("Analysis");

const answers = responseSheet.getRange(row, 6, 1, QUESTIONS.length).getValues()[0].join("\n");
const clientName = responseSheet.getRange(row, 4).getValue();
sendTelegramMessage(chatId, "Спасибо! Ваши ответы сохранены. Анализируем данные...");

try {
// вызываем GPT только один раз на полный анализ
const finalAnalysis = callOpenAI(
`Имя клиента: ${clientName}\nНа основе его ответов на кастдев, составь:
1) Сегментацию клиента в 1-2 предложения
2) 3 гипотезы улучшения сервиса ресторана
Ответ должен быть в формате:
Сегментация: ...
Гипотезы:
1. ...
2. ...
3. ...\n
Ответы клиента:
${answers}`
);

// записываем только этот финальный анализ в одну колонку, например E
analysisSheet.appendRow([new Date(), chatId, clientName, answers, finalAnalysis]);

sendTelegramMessage(chatId, "Спасибо! Вам будут добавлены 1000 бонусных баллов после проверки ответов.");

} catch (err) {
sendTelegramMessage(chatId, "Произошла ошибка при анализе данных: " + err);
}
}

// ================== Вспомогательные функции ==================
function findOrCreateRow(sheet, chatId) {
const lastRow = sheet.getLastRow();
if (lastRow < 2) {
sheet.appendRow([new Date(), chatId]);
return sheet.getLastRow();
}
const data = sheet.getRange(2, 2, lastRow - 1, 1).getValues();
for (let i = 0; i < data.length; i++) {
if (data[i][0] == chatId) return i + 2;
}
sheet.appendRow([new Date(), chatId]);
return sheet.getLastRow();
}

function sendTelegramMessage(chatId, text) {
const url = `https://api.telegram.org/bot${TOKEN}/sendMessage`;
const payload = { chat_id: chatId, text: text };
UrlFetchApp.fetch(url, {
method: "post",
contentType: "application/json",
payload: JSON.stringify(payload)
});
}

function callOpenAI(userInput) {
const url = "https://api.openai.com/v1/chat/completions";
const payload = {
model: "gpt-3.5-turbo",
messages: [
{ role: "system", content: SYSTEM_PROMPT },
{ role: "user", content: userInput }
],
temperature: 0.7
};
const options = {
method: "post",
contentType: "application/json",
headers: { "Authorization": `Bearer ${OPENAI_KEY}` },
payload: JSON.stringify(payload)
};
const response = UrlFetchApp.fetch(url, options);
const json = JSON.parse(response.getContentText());
return json.choices[0].message.content.trim();
}

/**
* =GPT_LIST(prompt)
* Возвращает список гипотез построчно
*/
function GPT_LIST(prompt) {
const result = GPT(
"Сформируй 3 короткие гипотезы улучшения сервиса ресторана списком:\n" + prompt
);
return result;
}

/**
* =GPT(prompt)
*/
function GPT(prompt) {
const url = "https://api.openai.com/v1/chat/completions";
const payload = {
model: "gpt-3.5-turbo",
messages: [
{ role: "system", content: "Ты аналитик кастдева ресторана." },
{ role: "user", content: prompt }
],
temperature: 0.5
};

const response = UrlFetchApp.fetch(url, {
method: "post",
contentType: "application/json",
headers: {
Authorization: `Bearer ${OPENAI_KEY}`
},
payload: JSON.stringify(payload)
});

const json = JSON.parse(response.getContentText());
return json.choices[0].message.content;
}

/**
* =GPT_CASTDEV(F2; G2)
* Генерирует вопросы кастдева на основе сегментации и гипотез
*/
function GPT_CASTDEV(segmentation, hypotheses) {
if (!segmentation || !hypotheses) {
return "Нет данных для генерации вопросов";
}

const prompt = `
Ты — эксперт по проведению кастдева для ресторана.

Данные анализа клиента:
Сегментация:
${segmentation}

Гипотезы:
${hypotheses}

Задача:
Сформируй 5–7 качественных вопросов кастдева, которые:
- проверяют гипотезы
- помогают глубже понять потребности клиента
- подходят для живого диалога

Формат:
1. ...
2. ...
3. ...
`;

const url = "https://api.openai.com/v1/chat/completions";
const payload = {
model: "gpt-3.5-turbo",
messages: [
{ role: "system", content: "Ты профессиональный кастдев-аналитик ресторана." },
{ role: "user", content: prompt }
],
temperature: 0.4
};

const response = UrlFetchApp.fetch(url, {
method: "post",
contentType: "application/json",
headers: {
Authorization: `Bearer ${OPENAI_KEY}`
},
payload: JSON.stringify(payload)
});

const json = JSON.parse(response.getContentText());
return json.choices[0].message.content.trim();
}

