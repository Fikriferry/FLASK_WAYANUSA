// Quiz Play JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Get level ID from URL parameters
    const urlParams = new URLSearchParams(window.location.search);
    const levelId = urlParams.get('level');
    const userId = document.body.dataset.userId;

    if (!levelId) {
        alert('Level tidak valid!');
        window.location.href = '/quiz';
        return;
    }

    let quizData = [];
    let currentQuestion = 0;
    let score = 0;
    let timeLeft = 30;
    let timer;
    let selectedAnswer = null;
    let userAnswers = []; // Array to track individual answers

    const questionText = document.getElementById('question-text');
    const answerButtons = document.querySelectorAll('.answer-btn');
    const questionCounter = document.querySelector('.question-counter');
    const timeLeftDisplay = document.getElementById('time-left');
    const resultModal = document.getElementById('result-modal');
    const resultTitle = document.getElementById('result-title');
    const resultDetails = document.getElementById('result-details');
    const resultIcon = document.getElementById('result-icon');
    const nextBtn = document.getElementById('next-btn');
    const scoreModal = document.getElementById('score-modal');
    const finalScore = document.getElementById('final-score');
    const progressFill = document.getElementById('progress-fill');
    const motivationText = document.getElementById('motivation-text');
    const playAgainBtn = document.getElementById('play-again-btn');
    const backToQuizBtn = document.getElementById('back-to-quiz-btn');

    // Fetch questions from API
    async function fetchQuestions() {
        try {
            const response = await fetch(`/api/quiz/get_questions?level=${levelId}`);
            if (!response.ok) {
                throw new Error('Failed to fetch questions');
            }
            const data = await response.json();
            quizData = data.questions;
            initQuiz();
        } catch (error) {
            console.error('Error fetching questions:', error);
            alert('Gagal memuat pertanyaan. Silakan coba lagi.');
            window.location.href = '/quiz';
        }
    }

    // Initialize quiz
    function initQuiz() {
        currentQuestion = 0;
        score = 0;
        selectedAnswer = null;
        userAnswers = []; // Reset answers array
        loadQuestion();
        startTimer();
    }

    // Load current question
    function loadQuestion() {
        const question = quizData[currentQuestion];
        questionText.textContent = question.question;
        questionCounter.textContent = `Pertanyaan ${currentQuestion + 1}/${quizData.length}`;

        // Map API response to answer buttons
        const answers = [
            { key: 'A', text: question.a },
            { key: 'B', text: question.b },
            { key: 'C', text: question.c },
            { key: 'D', text: question.d }
        ];

        answerButtons.forEach((btn, index) => {
            btn.textContent = `${answers[index].key}. ${answers[index].text}`;
            btn.dataset.answer = answers[index].key;
            btn.disabled = false;
            btn.style.background = '#E0E0E0';
            btn.style.color = '#333';
        });

        resetTimer();
    }

    // Start timer
    function startTimer() {
        timeLeft = 30;
        timeLeftDisplay.textContent = timeLeft;

        timer = setInterval(() => {
            timeLeft--;
            timeLeftDisplay.textContent = timeLeft;

            if (timeLeft <= 0) {
                clearInterval(timer);
                showResult(false, null);
            }
        }, 1000);
    }

    // Reset timer
    function resetTimer() {
        clearInterval(timer);
        startTimer();
    }

    // Show result modal
    function showResult(isCorrect, selectedAnswer) {
        clearInterval(timer);
        resultModal.style.display = 'flex';

        // Store the answer in userAnswers array
        userAnswers.push({
            question_id: quizData[currentQuestion].id,
            user_answer: selectedAnswer,
            is_correct: isCorrect
        });

        if (isCorrect) {
            resultIcon.textContent = '✓';
            resultTitle.textContent = 'Benar!';
            resultDetails.textContent = 'Jawaban kamu tepat!';
            score++;
        } else {
            resultIcon.textContent = '✗';
            resultTitle.textContent = 'Salah!';
            const correctAnswer = quizData[currentQuestion].correct_answer;
            if (selectedAnswer) {
                const selectedText = getAnswerText(selectedAnswer);
                const correctAnswerText = getAnswerText(correctAnswer);
                resultDetails.innerHTML = `
                    Jawaban kamu: <strong>${selectedText}</strong><br>
                    Jawaban benar: <strong>${correctAnswerText}</strong>
                `;
            } else {
                const correctAnswerText = getAnswerText(correctAnswer);
                resultDetails.innerHTML = `
                    Waktu habis!<br>
                    Jawaban benar: <strong>${correctAnswerText}</strong>
                `;
            }
        }
    }

    // Helper function to get answer text
    function getAnswerText(answerKey) {
        if (!answerKey) return '';
        const key = answerKey.toUpperCase();
        const question = quizData[currentQuestion];
        switch(key) {
            case 'A': return question.a;
            case 'B': return question.b;
            case 'C': return question.c;
            case 'D': return question.d;
            default: return '';
        }
    }

    // Helper function to get answer text for any question
    function getAnswerTextForQuestion(questionId, answerKey) {
        if (!answerKey) return '';
        const key = answerKey.toUpperCase();
        const question = quizData.find(q => q.id === questionId);
        if (!question) return '';
        switch(key) {
            case 'A': return question.a;
            case 'B': return question.b;
            case 'C': return question.c;
            case 'D': return question.d;
            default: return '';
        }
    }

    // Show final score
    function showFinalScore() {
        resultModal.style.display = 'none';
        scoreModal.style.display = 'flex';

        finalScore.textContent = score;
        const percentage = (score / quizData.length) * 100;
        progressFill.style.width = `${percentage}%`;

        if (score >= 8) {
            motivationText.textContent = 'Luar biasa! Kamu benar-benar paham materi ini!';
        } else if (score >= 5) {
            motivationText.textContent = 'Bagus! Sedikit lagi jadi ahli!';
        } else {
            motivationText.textContent = 'Jangan menyerah, coba lagi yuk!';
        }

        // Submit score to API
        submitScore();

        // Add confetti animation
        createConfetti();
    }

    // Submit score to API
    async function submitScore() {
        try {
            const response = await fetch('/api/quiz/submit', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    level_id: levelId,
                    user_id: userId,
                    score: score,
                    total_questions: quizData.length,
                    user_answers: userAnswers.map(ans => ({
                        question_id: ans.question_id,
                        user_answer: getAnswerTextForQuestion(ans.question_id, ans.user_answer),
                        is_correct: ans.is_correct
                    }))
                })
            });

            if (!response.ok) {
                console.error('Failed to submit score');
            }
        } catch (error) {
            console.error('Error submitting score:', error);
        }
    }



    // Create confetti effect
    function createConfetti() {
        for (let i = 0; i < 50; i++) {
            const confetti = document.createElement('div');
            confetti.className = 'confetti';
            confetti.style.left = Math.random() * 100 + 'vw';
            confetti.style.animationDelay = Math.random() * 3 + 's';
            confetti.style.background = ['#D4A373', '#C37A48', '#6B4226', '#FBEBE3'][Math.floor(Math.random() * 4)];
            document.body.appendChild(confetti);

            setTimeout(() => {
                confetti.remove();
            }, 3000);
        }
    }

    // Event listeners
    answerButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            if (selectedAnswer) return; // Prevent multiple selections

            selectedAnswer = this.dataset.answer;
            clearInterval(timer);

            // Disable all buttons
            answerButtons.forEach(b => b.disabled = true);

            // Highlight selected answer
            this.style.background = '#D4A373';
            this.style.color = 'white';

            // Check if correct (case-insensitive to prevent uppercase 'A' vs lowercase 'a' database mismatch)
            const isCorrect = selectedAnswer.toUpperCase() === quizData[currentQuestion].correct_answer.toUpperCase();
            setTimeout(() => {
                showResult(isCorrect, selectedAnswer);
            }, 500);
        });
    });

    nextBtn.addEventListener('click', function() {
        resultModal.style.display = 'none';
        selectedAnswer = null;

        currentQuestion++;
        if (currentQuestion < quizData.length) {
            loadQuestion();
        } else {
            showFinalScore();
        }
    });

    playAgainBtn.addEventListener('click', function() {
        scoreModal.style.display = 'none';
        initQuiz();
    });

    backToQuizBtn.addEventListener('click', function() {
        window.location.href = '/quiz';
    });

    // Start by fetching questions
    fetchQuestions();
});
