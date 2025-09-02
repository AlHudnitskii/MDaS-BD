from django.db import models

class Role(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name = "Role name")

    class Meta:
        verbose_name = "Role"
        verbose_name_plural = "Roles"

    def __str__(self):
        return self.name

class User(models.Model):
    first_name = models.CharField(max_length=50, unique=True, verbose_name = "First name")
    last_name = models.CharField(max_length=50, unique=True, verbose_name = "Last name")
    email = models.EmailField(unique=True, verbose_name = "Email")
    password = models.CharField(max_length=50, unique=True, verbose_name = "Password")
    role = models.ForeignKey(Role, on_delete=models.CASCADE, verbose_name = "Role")

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return self.first_name + " " + self.last_name

class Resource(models.Model):
    title = models.CharField(max_length=100, unique=True, verbose_name = "Title")
    authors = models.ManyToManyField(User, verbose_name = "Authors")
    publication_date = models.DateField(verbose_name = "Publication date")

    class Meta:
        verbose_name = "Resource"
        verbose_name_plural = "Resources"

    def __str__(self):
        return self.title

class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name = "Genre")

    class Meta:
        verbose_name = "Genre"
        verbose_name_plural = "Genres"

    def __str__(self):
        return self.name

class Borrowing(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name = "User")
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, verbose_name = "Resource")
    borrow_date = models.DateField(verbose_name = "Borrow date")
    return_date = models.DateField(verbose_name = "Return date")

    class Meta:
        verbose_name = "Borrowing"
        verbose_name_plural = "Borrowings"
        unique_together = ("user", "resource")

    def __str__(self):
        return f"Borrowing {self.resource.title} by {self.user.first_name} {self.user.last_name} "

class Fine(models.Model):
    borrowing = models.ForeignKey(Borrowing, on_delete=models.CASCADE, verbose_name = "Borrowing")
    amount = models.IntegerField(verbose_name = "Amount")
    reason = models.TextField(verbose_name = "Reason")
    issued_date = models.DateField(verbose_name = "Issued date")
    paid = models.BooleanField(verbose_name = "Paid", default=False)

    class Meta:
        verbose_name = "Fine"
        verbose_name_plural = "Fines"

    def __str__(self):
        return f"Fine {self.amount} for {self.borrowing.id}"