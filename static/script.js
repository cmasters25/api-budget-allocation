async function sendMessage() {


    const team = document.getElementById("team").value;
    const provider = document.getElementById("provider").value;
    const model = document.getElementById("model").value;

    const message = document.getElementById("message").value;

    const fileInput = document.getElementById("file");


    const chatBox = document.getElementById("chat-box");


    if (!message) {
        alert("Enter a message");
        return;
    }


    // show user message

    chatBox.innerHTML += `
        <div class="message user">
            <b>You:</b><br>
            ${message}
        </div>
    `;


    const formData = new FormData();


    formData.append("team", team);
    formData.append("provider", provider);
    formData.append("model", model);
    formData.append("message", message);


    if (fileInput.files.length > 0) {
        formData.append(
            "file",
            fileInput.files[0]
        );
    }



    try {


        const response = await fetch(
            "https://YOUR-RENDER-URL.onrender.com/chat",
            {
                method: "POST",
                body: formData
            }
        );


        const data = await response.json();



        if (data.response) {


            chatBox.innerHTML += `
            <div class="message ai">
                <b>AI:</b><br>
                ${data.response}
                <br><br>
                Cost: $${data.cost.toFixed(5)}
            </div>
            `;


            document.getElementById("budget-info").innerHTML =
                `
            Team: ${data.team}<br>
            Spent: $${data.spent.toFixed(5)}<br>
            Remaining: $${data.remaining.toFixed(5)}
            `;

        }

        else {

            chatBox.innerHTML += `
            <div class="message ai">
                Error:
                ${data.error}
            </div>
            `;

        }



    }

    catch (error) {

        chatBox.innerHTML += `
        <div class="message ai">
            Connection error:
            ${error}
        </div>
        `;

    }



    document.getElementById("message").value = "";


}