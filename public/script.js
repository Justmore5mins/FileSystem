window.addEventListener("load", () => {
    fetch("/api/getAll", {
        method:"GET"
    })
        .then(r => r.json())
        .then(r => {
            for (const record of r) {
                document.querySelector("table").insertAdjacentHTML("beforeend", `
                    <tr>
                        <td>${record.name}</td>
                        <td>${record.type}</td>
                        <td>${record.content}</td>
                    </tr>
                `)
            }
        }).catch(r => {
        });
});
